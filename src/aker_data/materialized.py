"""Helpers for building and refreshing materialized analytics tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

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
    Markets,
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

            refreshed_at = datetime.now(timezone.utc)
            insert_stmt = text(
                """
                INSERT INTO market_analytics (
                    msa_id,
                    market_name,
                    population,
                    households,
                    vacancy_rate,
                    permit_per_1k,
                    tech_cagr,
                    walk_15_ct,
                    trail_mi_pc,
                    supply_score,
                    jobs_score,
                    urban_score,
                    outdoor_score,
                    composite_score,
                    period_month,
                    refreshed_at,
                    run_id
                )
                SELECT
                    m.msa_id,
                    m.name,
                    MAX(m.pop) AS population,
                    MAX(m.households) AS households,
                    AVG(ms.vacancy_rate) AS vacancy_rate,
                    AVG(ms.permit_per_1k) AS permit_per_1k,
                    AVG(mj.tech_cagr_5yr) AS tech_cagr,
                    AVG(mu.walk_15_ct) AS walk_15_ct,
                    AVG(mo.trail_mi_pc) AS trail_mi_pc,
                    AVG(ps.supply_0_5) AS supply_score,
                    AVG(ps.jobs_0_5) AS jobs_score,
                    AVG(ps.urban_0_5) AS urban_score,
                    AVG(ps.outdoor_0_5) AS outdoor_score,
                    COALESCE(
                        AVG(ps.weighted_0_5),
                        (
                            COALESCE(AVG(ps.supply_0_5), 0) +
                            COALESCE(AVG(ps.jobs_0_5), 0) +
                            COALESCE(AVG(ps.urban_0_5), 0) +
                            COALESCE(AVG(ps.outdoor_0_5), 0)
                        ) /
                        NULLIF(
                            (CASE WHEN AVG(ps.supply_0_5) IS NULL THEN 0 ELSE 1 END) +
                            (CASE WHEN AVG(ps.jobs_0_5) IS NULL THEN 0 ELSE 1 END) +
                            (CASE WHEN AVG(ps.urban_0_5) IS NULL THEN 0 ELSE 1 END) +
                            (CASE WHEN AVG(ps.outdoor_0_5) IS NULL THEN 0 ELSE 1 END),
                            0
                        )
                    ) AS composite_score,
                    :period_month AS period_month,
                    :refreshed_at AS refreshed_at,
                    :run_id AS run_id
                FROM markets m
                LEFT JOIN market_supply ms ON ms.msa_id = m.msa_id
                LEFT JOIN market_jobs mj ON mj.msa_id = m.msa_id
                LEFT JOIN market_urban mu ON mu.msa_id = m.msa_id
                LEFT JOIN market_outdoors mo ON mo.msa_id = m.msa_id
                LEFT JOIN pillar_scores ps ON ps.msa_id = m.msa_id
                GROUP BY m.msa_id, m.name
                """
            )
            session.execute(
                insert_stmt,
                {
                    "period_month": period_month,
                    "refreshed_at": refreshed_at,
                    "run_id": self.run_id,
                },
            )
            session.commit()

            analytics_rows = session.execute(
                select(
                    MarketAnalytics.msa_id,
                    MarketAnalytics.market_name,
                    MarketAnalytics.population,
                    MarketAnalytics.households,
                    MarketAnalytics.vacancy_rate,
                    MarketAnalytics.permit_per_1k,
                    MarketAnalytics.tech_cagr,
                    MarketAnalytics.walk_15_ct,
                    MarketAnalytics.trail_mi_pc,
                    MarketAnalytics.supply_score,
                    MarketAnalytics.jobs_score,
                    MarketAnalytics.urban_score,
                    MarketAnalytics.outdoor_score,
                    MarketAnalytics.composite_score,
                    MarketAnalytics.period_month,
                    MarketAnalytics.refreshed_at,
                    MarketAnalytics.run_id,
                ).where(MarketAnalytics.period_month == period_month)
            ).all()

            if not analytics_rows:
                return RefreshResult("market_analytics", 0, None)

            df = pd.DataFrame(
                analytics_rows,
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
                    "composite_score",
                    "period_month",
                    "refreshed_at",
                    "run_id",
                ],
            )

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

            validation = validate_dataset(df, "market_analytics")
            return RefreshResult("market_analytics", len(analytics_rows), validation)

    def refresh_asset_performance(self, *, period: date | datetime | str) -> RefreshResult:
        period_month = _ensure_month(period)
        with Session(self.engine) as session:
            # Older SQLite-based extras may not include period_month; defensively delete by run when absent
            try:
                session.execute(
                    delete(AssetPerformance).where(AssetPerformance.period_month == period_month)
                )
            except AttributeError:
                session.execute(delete(AssetPerformance))

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
