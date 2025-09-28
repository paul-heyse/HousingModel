"""Prefect flow for refreshing economic indicator datasets (ACS, BLS, BEA, LODES)."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Mapping, Sequence

import pandas as pd

from aker_core.config import get_settings
from aker_core.etl import (
    load_bea_regional,
    load_bls_qcew,
    load_bls_timeseries,
    load_census_acs,
    load_census_bfs,
    load_lodes,
)
from aker_data.lake import DataLake

from .base import ETLFlow, etl_task, timed_flow, with_run_context

DEFAULT_ACS_VARIABLES = ("B01001_001E", "B19013_001E", "B15003_017E")
DEFAULT_ACS_GEOS: tuple[Mapping[str, str], ...] = (
    {"geo": "metropolitan statistical area/micropolitan statistical area", "geo_id": "19740"},  # Denver-Aurora-Lakewood, CO
    {"geo": "metropolitan statistical area/micropolitan statistical area", "geo_id": "26420"},  # Houston-The Woodlands-Sugar Land, TX
)
DEFAULT_BLS_SERIES = ("LAUCN080050000000005",)  # Boulder County unemployment rate


class EconomicIndicatorsFlow(ETLFlow):
    """Refresh demographic, labor, and macro datasets using the shared ETL helpers."""

    def __init__(self) -> None:
        super().__init__(
            "refresh_economic_indicators",
            "Refresh ACS, BLS, BEA, and LODES datasets and store them in the data lake",
        )
        try:
            self._settings = get_settings()
        except Exception:  # pragma: no cover - defensive fallback for tests
            self._settings = None

    # ------------------------------------------------------------------
    @etl_task("load_acs", "Ingest ACS demographic variables")
    def ingest_acs(
        self,
        *,
        year: int,
        variables: Sequence[str],
        geo_requests: Sequence[Mapping[str, str]],
        as_of: str,
    ) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        api_key = None
        if self._settings and self._settings.census_api_key:
            api_key = self._settings.census_api_key.get_secret_value()

        for request in geo_requests:
            frame = load_census_acs(
                year=year,
                variables=variables,
                geo=request["geo"],
                geo_id=request["geo_id"],
                api_key=api_key,
                as_of=as_of,
            )
            frame["source"] = "census_acs"
            frames.append(frame)

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    @etl_task("load_bfs", "Ingest business formation statistics")
    def ingest_bfs(self, *, time_expr: str, as_of: str) -> pd.DataFrame:
        api_key = None
        if self._settings and self._settings.census_api_key:
            api_key = self._settings.census_api_key.get_secret_value()
        frame = load_census_bfs(time_expr=time_expr, api_key=api_key, as_of=as_of)
        frame["source"] = "census_bfs"
        return frame

    @etl_task("load_bls_timeseries", "Ingest BLS public data API series")
    def ingest_bls_timeseries(
        self,
        *,
        series_ids: Sequence[str],
        start_year: int,
        end_year: int,
        as_of: str,
    ) -> pd.DataFrame:
        frame = load_bls_timeseries(
            series_ids=series_ids,
            start_year=start_year,
            end_year=end_year,
            as_of=as_of,
        )
        if not frame.empty:
            frame["source"] = "bls_timeseries"
        return frame

    @etl_task("load_bls_qcew", "Ingest Quarterly Census of Employment and Wages")
    def ingest_bls_qcew(
        self,
        *,
        area_code: str,
        year: int,
        quarter: int,
        as_of: str,
    ) -> pd.DataFrame:
        frame = load_bls_qcew(area_code=area_code, year=year, quarter=quarter, as_of=as_of)
        if not frame.empty:
            frame["source"] = "bls_qcew"
        return frame

    @etl_task("load_lodes", "Ingest LEHD LODES data")
    def ingest_lodes(
        self,
        *,
        state: str,
        segment: str,
        part: str,
        as_of: str,
    ) -> pd.DataFrame:
        frame = load_lodes(state=state, segment=segment, part=part, as_of=as_of)
        if not frame.empty:
            frame["source"] = "lehd_lodes"
        return frame

    @etl_task("load_bea_regional", "Ingest BEA regional income/GDP")
    def ingest_bea(
        self,
        *,
        dataset_name: str,
        table_name: str,
        geo_fips: str,
        year: str,
        as_of: str,
    ) -> pd.DataFrame:
        api_key = None
        if self._settings and self._settings.bea_api_key:
            api_key = self._settings.bea_api_key.get_secret_value()
        frame = load_bea_regional(
            dataset_name=dataset_name,
            table_name=table_name,
            geo_fips=geo_fips,
            year=year,
            api_key=api_key,
            as_of=as_of,
        )
        if not frame.empty:
            frame["source"] = "bea_regional"
        return frame

    @etl_task("store_dataset", "Persist dataset in the data lake")
    def store_dataset(self, df: pd.DataFrame, dataset: str, as_of: str) -> str:
        if df.empty:
            return "SKIPPED"
        lake = DataLake()
        return lake.write(df, dataset, as_of)


@timed_flow
@with_run_context
def refresh_economic_indicators(
    *,
    acs_year: int | None = None,
    acs_variables: Sequence[str] | None = None,
    acs_geo_requests: Sequence[Mapping[str, str]] | None = None,
    bfs_time_expr: str | None = None,
    bls_series_ids: Sequence[str] | None = None,
    bls_start_year: int | None = None,
    bls_end_year: int | None = None,
    qcew_area_code: str | None = None,
    qcew_year: int | None = None,
    qcew_quarter: int | None = None,
    lodes_state: str | None = None,
    lodes_segment: str | None = None,
    lodes_part: str | None = None,
    bea_dataset_name: str | None = None,
    bea_table_name: str | None = None,
    bea_geo_fips: str | None = None,
    bea_year: str | None = None,
    as_of: str | None = None,
) -> dict[str, str | int]:
    flow = EconomicIndicatorsFlow()
    settings = flow._settings

    acs_year = acs_year or (settings.acs_default_year if settings else 2024)
    acs_vars = list(acs_variables) if acs_variables else (
        settings.acs_default_variables if settings and settings.acs_default_variables else list(DEFAULT_ACS_VARIABLES)
    )
    acs_geo_requests = acs_geo_requests or (
        settings.acs_default_geo_requests if settings and settings.acs_default_geo_requests else DEFAULT_ACS_GEOS
    )
    bfs_time_expr = bfs_time_expr or (
        settings.bfs_default_time_expr if settings and settings.bfs_default_time_expr else "from 2024-01 to 2024-12"
    )
    bls_series = list(bls_series_ids) if bls_series_ids else (
        settings.bls_series_ids if settings and settings.bls_series_ids else list(DEFAULT_BLS_SERIES)
    )
    bls_start_year = bls_start_year or (settings.bls_start_year if settings and settings.bls_start_year else 2023)
    bls_end_year = bls_end_year or (settings.bls_end_year if settings and settings.bls_end_year else 2024)
    qcew_area_code = qcew_area_code or (settings.qcew_area_code if settings and settings.qcew_area_code else "08001")
    qcew_year = qcew_year or (settings.qcew_year if settings and settings.qcew_year else bls_end_year)
    qcew_quarter = qcew_quarter or (settings.qcew_quarter if settings and settings.qcew_quarter else 1)
    lodes_state = lodes_state or (settings.lodes_state if settings and settings.lodes_state else "co")
    lodes_segment = lodes_segment or (settings.lodes_segment if settings and settings.lodes_segment else "wac")
    lodes_part = lodes_part or (settings.lodes_part if settings and settings.lodes_part else "main")
    bea_dataset_name = bea_dataset_name or (settings.bea_dataset_name if settings and settings.bea_dataset_name else "Regional")
    bea_table_name = bea_table_name or (settings.bea_table_name if settings and settings.bea_table_name else "CAINC1")
    bea_geo_fips = bea_geo_fips or (settings.bea_geo_fips if settings and settings.bea_geo_fips else "MSA")
    bea_year = bea_year or (settings.bea_year if settings and settings.bea_year else "2024")

    as_of_value = as_of or datetime.now().strftime("%Y-%m")
    flow.log_start(acs_year=acs_year, as_of=as_of_value)
    started = time.time()

    try:
        acs_df = flow.ingest_acs(
            year=acs_year,
            variables=list(acs_vars),
            geo_requests=list(acs_geo_requests),
            as_of=as_of_value,
        )
        bfs_df = flow.ingest_bfs(time_expr=bfs_time_expr, as_of=as_of_value)
        bls_ts_df = flow.ingest_bls_timeseries(
            series_ids=list(bls_series),
            start_year=bls_start_year,
            end_year=bls_end_year,
            as_of=as_of_value,
        )
        bls_qcew_df = flow.ingest_bls_qcew(
            area_code=qcew_area_code,
            year=qcew_year,
            quarter=qcew_quarter,
            as_of=as_of_value,
        )
        lodes_df = flow.ingest_lodes(
            state=lodes_state,
            segment=lodes_segment,
            part=lodes_part,
            as_of=as_of_value,
        )
        bea_df = flow.ingest_bea(
            dataset_name=bea_dataset_name,
            table_name=bea_table_name,
            geo_fips=bea_geo_fips,
            year=bea_year,
            as_of=as_of_value,
        )

        flow.store_dataset(acs_df, dataset="demographics_acs", as_of=as_of_value)
        flow.store_dataset(bfs_df, dataset="business_formation", as_of=as_of_value)
        flow.store_dataset(bls_ts_df, dataset="bls_timeseries", as_of=as_of_value)
        flow.store_dataset(bls_qcew_df, dataset="bls_qcew", as_of=as_of_value)
        flow.store_dataset(lodes_df, dataset="lodes", as_of=as_of_value)
        flow.store_dataset(bea_df, dataset="bea_regional", as_of=as_of_value)

        duration = time.time() - started
        flow.log_complete(
            duration,
            as_of=as_of_value,
            acs_rows=len(acs_df),
            bfs_rows=len(bfs_df),
            bls_series_rows=len(bls_ts_df),
            bls_qcew_rows=len(bls_qcew_df),
            lodes_rows=len(lodes_df),
            bea_rows=len(bea_df),
        )
        return {
            "as_of": as_of_value,
            "acs_rows": len(acs_df),
            "bfs_rows": len(bfs_df),
            "bls_series_rows": len(bls_ts_df),
            "bls_qcew_rows": len(bls_qcew_df),
            "lodes_rows": len(lodes_df),
            "bea_rows": len(bea_df),
        }

    except Exception as exc:  # pragma: no cover - logging path
        duration = time.time() - started
        flow.log_error(str(exc), duration, as_of=as_of_value)
        raise


__all__ = ["EconomicIndicatorsFlow", "refresh_economic_indicators"]
