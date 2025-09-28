from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from aker_core.validation import validate_dataset
from aker_data.lake import DataLake
from aker_data.models import Assets
from deal import ScopeTemplate, rank_scopes_with_etl

from .base import ETLFlow, etl_task, timed_flow, with_run_context


class DealRankRefreshFlow(ETLFlow):
    def __init__(self) -> None:
        super().__init__("deal_rank_refresh", "Refresh deal scope rankings with ETL adjustments")

    @etl_task("list_assets", "List assets to rank")
    def list_assets(self, limit: Optional[int] = None) -> List[int]:
        engine = create_engine("sqlite:///flows.db")
        with Session(engine) as session:
            q = select(Assets.asset_id).limit(limit) if limit else select(Assets.asset_id)
            return [row[0] for row in session.execute(q).all()]

    @etl_task("compute_rankings", "Compute ETL-adjusted scope rankings")
    def compute_rankings(
        self,
        asset_ids: Sequence[int],
        as_of: Optional[str] = None,
    ) -> pd.DataFrame:
        lake = DataLake()

        # Example library of scopes; in production load from DB or config
        scope_library = [
            ScopeTemplate(name="LED Retrofit", cost=50000, annual_savings=12000),
            ScopeTemplate(name="Controls Tuning", cost=15000, annual_savings=6000),
            ScopeTemplate(name="Water Fixtures", cost=20000, annual_savings=7000),
        ]

        records: list[dict] = []
        for asset_id in asset_ids:
            ranked = rank_scopes_with_etl(
                str(asset_id),
                scope_library,
                lake=lake,
                as_of=as_of,
                asset_category="garden",
            )
            for idx, r in enumerate(ranked, start=1):
                records.append(
                    {
                        "asset_id": asset_id,
                        "scope_name": r.name,
                        "roi": r.roi,
                        "payback_years": r.payback_years,
                        "downtime_hours": r.downtime_hours,
                        "cost": r.cost,
                        "rank": idx,
                        "as_of": as_of or datetime.now(timezone.utc).strftime("%Y-%m"),
                        "refreshed_at": datetime.now(timezone.utc),
                    }
                )

        return pd.DataFrame.from_records(records)

    @etl_task("validate_rankings", "Validate ETL-adjusted rankings dataset")
    def validate_rankings(self, df: pd.DataFrame) -> None:
        # Reuse existing validation infra; suite name can be added later
        validate_dataset(df, "deal_rankings")


@timed_flow
@with_run_context
def refresh_deal_rankings(limit: Optional[int] = None, as_of: Optional[str] = None) -> str:
    drf = DealRankRefreshFlow()
    drf.log_start(limit=limit, as_of=as_of)

    asset_ids = drf.list_assets(limit)
    df = drf.compute_rankings(asset_ids, as_of)
    drf.validate_rankings(df)

    # Persist to data lake
    lake = DataLake()
    partition = lake.write(df, "deal_rankings", as_of=as_of or datetime.now(timezone.utc).strftime("%Y-%m"))

    drf.log_complete(0.0, rows=len(df))
    return partition


