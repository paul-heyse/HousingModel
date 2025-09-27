"""Prefect flow for refreshing materialized analytics tables."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from aker_core.config import get_settings
from aker_data.engine import create_engine_from_url
from aker_data.materialized import MaterializedTableManager

from .base import ETLFlow, etl_task, get_current_run_context, timed_flow, with_run_context


def _default_database_url() -> str:
    try:
        settings = get_settings()
        return settings.postgis_dsn.get_secret_value()
    except Exception:
        return "sqlite:///flows.db"


class MaterializedAnalyticsFlow(ETLFlow):
    def __init__(self) -> None:
        super().__init__(
            "refresh_materialized_tables",
            "Build and validate materialized analytics tables",
        )

    def _manager(self, database_url: Optional[str]) -> MaterializedTableManager:
        url = database_url or _default_database_url()
        engine = create_engine_from_url(url)
        run_context = get_current_run_context()
        run_id = run_context.id if run_context else None
        return MaterializedTableManager(engine, run_id=run_id)

    @etl_task("refresh_market_analytics", "Populate market analytics materialized table")
    def build_market_analytics(
        self, as_of: str, database_url: Optional[str] = None
    ) -> Dict[str, object]:
        manager = self._manager(database_url)
        result = manager.refresh_market_analytics(period=as_of)
        return result.as_dict()

    @etl_task("refresh_asset_performance", "Populate asset performance materialized table")
    def build_asset_performance(
        self, as_of: str, database_url: Optional[str] = None
    ) -> Dict[str, object]:
        manager = self._manager(database_url)
        result = manager.refresh_asset_performance(period=as_of)
        return result.as_dict()


@timed_flow
@with_run_context
def refresh_materialized_tables(
    as_of: Optional[str] = None, database_url: Optional[str] = None
) -> Dict[str, object]:
    if as_of is None:
        as_of = datetime.utcnow().strftime("%Y-%m")

    flow_runner = MaterializedAnalyticsFlow()
    start_ts = datetime.utcnow()
    flow_runner.log_start(as_of=as_of)

    try:
        market_result = flow_runner.build_market_analytics(as_of, database_url)
        asset_result = flow_runner.build_asset_performance(as_of, database_url)
        duration = (datetime.utcnow() - start_ts).total_seconds()
        flow_runner.log_complete(
            duration,
            as_of=as_of,
            market_rows=market_result["rows"],
            asset_rows=asset_result["rows"],
        )
        return {"market_analytics": market_result, "asset_performance": asset_result}
    except Exception as exc:  # pragma: no cover - surface to caller
        duration = (datetime.utcnow() - start_ts).total_seconds()
        flow_runner.log_error(str(exc), duration, as_of=as_of)
        raise


if __name__ == "__main__":
    refresh_materialized_tables()
