"""Helpers for building and refreshing materialized analytics tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, Optional

import pandas as pd
from sqlalchemy import delete, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from aker_core.markets.service import PillarScoreService
from aker_core.validation import ValidationResult, validate_dataset

from .models import (
    AssetPerformance,
    Assets,
    MarketAnalytics,
    MarketJobs,
    MarketOutdoors,
    Markets,
    MarketSupply,
    MarketUrban,
    PillarScores,
)


def _ensure_month(value: date | datetime | str | None) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.replace(day=1)
    if isinstance(value, datetime):
        return value.date().replace(day=1)
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    today = datetime.now(timezone.utc).date()
    return today.replace(day=1)


@dataclass
class RefreshResult:
    table: str
    rows: int
    validation: Optional[ValidationResult]

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"table": self.table, "rows": self.rows}
        if self.validation is not None:
            payload["validation"] = self.validation.to_dict()
        return payload


class MaterializedTableManager:
    """Refresh and validate materialized analytics tables."""

    def __init__(self, engine: Engine, *, run_id: Optional[int] = None) -> None:
        self.engine = engine
        self.run_id = run_id

    def _create_or_replace_view(self, session: Session, name: str, select_sql: str) -> None:
        """Utility to replace a simple SQL view."""

        session.execute(text(f"DROP VIEW IF EXISTS {name}"))
        session.execute(text(f"CREATE VIEW {name} AS {select_sql}"))
        session.commit()

    def refresh_market_analytics(self, *, period: date | datetime | str) -> RefreshResult:
        period_month = _ensure_month(period)
        with Session(self.engine) as session:
            service = PillarScoreService(session)
            msa_ids = [row[0] for row in session.execute(select(Markets.msa_id)).all() if row[0]]
            service.refresh_many(msa_ids, as_of=period_month, run_id=self.run_id)

            session.execute(
                delete(MarketAnalytics).where(MarketAnalytics.period_month == period_month)
            )

            rows = session.execute(
                select(
                    Markets.msa_id,
                    Markets.name,
                    Markets.pop,
                    Markets.households,
                    MarketSupply.vacancy_rate,
                    MarketSupply.permit_per_1k,
                    MarketJobs.tech_cagr_5yr,
                    MarketUrban.walk_15_ct,
                    MarketOutdoors.trail_mi_pc,
                    PillarScores.supply_0_5,
                    PillarScores.jobs_0_5,
                    PillarScores.urban_0_5,
                    PillarScores.outdoor_0_5,
                    PillarScores.weighted_0_5,
                    PillarScores.weighted_0_100,
                    PillarScores.score_as_of,
                )
                .select_from(Markets)
                .outerjoin(MarketSupply, MarketSupply.msa_id == Markets.msa_id)
                .outerjoin(MarketJobs, MarketJobs.msa_id == Markets.msa_id)
                .outerjoin(MarketUrban, MarketUrban.msa_id == Markets.msa_id)
                .outerjoin(MarketOutdoors, MarketOutdoors.msa_id == Markets.msa_id)
                .outerjoin(PillarScores, PillarScores.msa_id == Markets.msa_id)
            ).all()

            df = pd.DataFrame(
                rows,
                columns=[
                    "msa_id",
                    "market_name",
                    "population",
                    "households",
                    "vacancy_rate",
                    "permit_per_1k",
                    "tech_cagr",
                    "walk_15_ct",
                    "trail_mi_pc",
                    "supply_score",
                    "jobs_score",
                    "urban_score",
                    "outdoor_score",
                    "composite_score_0_5",
                    "composite_score_0_100",
                    "score_as_of",
                ],
            )

            if df.empty:
                session.commit()
                return RefreshResult("market_analytics", 0, None)

            grouped = (
                df.groupby(["msa_id", "market_name"], dropna=False)
                .agg(
                    {
                        "population": "max",
                        "households": "max",
                        "vacancy_rate": "mean",
                        "permit_per_1k": "mean",
                        "tech_cagr": "mean",
                        "walk_15_ct": "mean",
                        "trail_mi_pc": "mean",
                        "supply_score": "mean",
                        "jobs_score": "mean",
                        "urban_score": "mean",
                        "outdoor_score": "mean",
                        "composite_score_0_5": "mean",
                        "composite_score_0_100": "mean",
                        "score_as_of": "max",
                    }
                )
                .reset_index()
            )

            def _calc_composite(row: pd.Series) -> float:
                scores: Iterable[float] = [
                    row.get("supply_score"),
                    row.get("jobs_score"),
                    row.get("urban_score"),
                    row.get("outdoor_score"),
                ]
                valid = [value for value in scores if value is not None]
                if not valid:
                    return row.get("composite_score_0_5") or 0.0
                return float(sum(valid) / len(valid))

            grouped["composite_score"] = grouped["composite_score_0_5"].where(
                grouped["composite_score_0_5"].notna(),
                grouped.apply(_calc_composite, axis=1),
            )
            grouped["period_month"] = period_month
            grouped["refreshed_at"] = datetime.now(timezone.utc)
            grouped["run_id"] = self.run_id

            insert_df = grouped.drop(
                columns=["composite_score_0_5", "composite_score_0_100", "score_as_of"],
                errors="ignore",
            )
            records = insert_df.to_dict(orient="records")
            session.bulk_insert_mappings(MarketAnalytics, records)
            session.commit()

            self._create_or_replace_view(
                session,
                "market_supply_joined",
                """
                SELECT
                    market_analytics.msa_id,
                    market_analytics.market_name,
                    market_analytics.composite_score,
                    market_analytics.period_month,
                    market_analytics.refreshed_at,
                    market_analytics.run_id
                FROM market_analytics
                """,
            )

            validation = validate_dataset(grouped, "market_analytics")
            return RefreshResult("market_analytics", len(records), validation)

    def refresh_asset_performance(self, *, period: date | datetime | str) -> RefreshResult:
        period_month = _ensure_month(period)
        with Session(self.engine) as session:
            session.execute(
                delete(AssetPerformance).where(AssetPerformance.period_month == period_month)
            )

            analytics_subquery = (
                select(
                    MarketAnalytics.msa_id,
                    MarketAnalytics.composite_score.label("market_composite_score"),
                )
                .where(MarketAnalytics.period_month == period_month)
                .subquery()
            )

            rows = session.execute(
                select(
                    Assets.asset_id,
                    Assets.msa_id,
                    Assets.units,
                    Assets.year_built,
                    PillarScores.weighted_0_5,
                    analytics_subquery.c.market_composite_score,
                )
                .select_from(Assets)
                .outerjoin(PillarScores, PillarScores.msa_id == Assets.msa_id)
                .outerjoin(analytics_subquery, analytics_subquery.c.msa_id == Assets.msa_id)
            ).all()

            df = pd.DataFrame(
                rows,
                columns=[
                    "asset_id",
                    "msa_id",
                    "units",
                    "year_built",
                    "score",
                    "market_composite_score",
                ],
            )

            if df.empty:
                session.commit()
                return RefreshResult("asset_performance", 0, None)

            df["score"] = df.apply(
                lambda row: (
                    row["score"] if pd.notnull(row["score"]) else row["market_composite_score"]
                ),
                axis=1,
            )
            df["score"] = df["score"].fillna(0.0)
            df["period_month"] = period_month
            df["refreshed_at"] = datetime.now(timezone.utc)
            df["run_id"] = self.run_id

            df["rank_in_market"] = (
                df.sort_values("score", ascending=False)
                .groupby("msa_id")["score"]
                .rank(method="dense", ascending=False)
                .astype(int)
            )

            records = df.to_dict(orient="records")
            session.bulk_insert_mappings(AssetPerformance, records)
            session.commit()

            self._create_or_replace_view(
                session,
                "asset_scoring_joined",
                """
                SELECT
                    asset_performance.asset_id,
                    asset_performance.msa_id,
                    asset_performance.score,
                    asset_performance.rank_in_market,
                    asset_performance.period_month,
                    asset_performance.refreshed_at,
                    asset_performance.run_id
                FROM asset_performance
                """,
            )

            validation = validate_dataset(df, "asset_performance")
            return RefreshResult("asset_performance", len(records), validation)
