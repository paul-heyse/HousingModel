"""Prefect flow to orchestrate boundary dataset ingestion."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Dict, Sequence, Tuple

from aker_core.cache import get_cache
from aker_core.etl.boundaries import refresh_boundary_sources
from aker_data.lake import DataLake

from .base import etl_task, timed_flow, with_run_context


@etl_task("refresh-boundary-sources", "Load TIGERweb, OpenAddresses, Microsoft footprints")
@with_run_context
def refresh_boundaries_task(
    *,
    state_fips: Sequence[str],
    openaddresses_runs: Sequence[Tuple[str, str]],
    building_countries: Sequence[str],
    as_of: str,
) -> Dict[str, int]:
    cache = get_cache()
    lake = DataLake()
    return refresh_boundary_sources(
        lake=lake,
        cache=cache,
        state_fips=state_fips,
        openaddresses_runs=openaddresses_runs,
        building_countries=building_countries,
        as_of=as_of,
    )


@timed_flow
def refresh_boundary_catalog(
    state_fips: Sequence[str] = ("06", "12", "36"),
    openaddresses_runs: Sequence[Tuple[str, str]] = (),
    building_countries: Sequence[str] = ("US",),
    as_of: str | None = None,
) -> Dict[str, int]:
    resolved_as_of = as_of or datetime.now(UTC).strftime("%Y-%m")
    summary = refresh_boundaries_task(
        state_fips=state_fips,
        openaddresses_runs=openaddresses_runs,
        building_countries=building_countries,
        as_of=resolved_as_of,
    )
    return summary


__all__ = ["refresh_boundary_catalog"]

