"""Prefect flow for refreshing hazard severity metrics feeding the Risk Engine."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Sequence, Tuple

import pandas as pd

from aker_data.lake import DataLake

from aker_core.etl.hazards import (
    load_hail_frequency,
    load_policy_risk as load_policy_risk_hazard,
    load_snow_load,
    load_water_stress,
    load_wildfire_wui,
)

from .base import ETLFlow, etl_task, timed_flow, with_run_context

DEFAULT_SUBJECTS: Tuple[Tuple[str, str], ...] = (
    ("market", "MSA001"),
    ("market", "MSA002"),
    ("asset", "1"),
)


class HazardMetricsFlow(ETLFlow):
    def __init__(self) -> None:
        super().__init__(
            "refresh_hazard_metrics",
            "Refresh synthetic hazard severity metrics for wildfire, hail, snow load, water stress, and policy risk.",
        )

    @etl_task("load_wildfire", "Load wildfire WUI severity metrics")
    def load_wildfire(self, subjects: Sequence[Tuple[str, str]], as_of: str) -> pd.DataFrame:
        return load_wildfire_wui(subjects=list(subjects), as_of=as_of)

    @etl_task("load_hail", "Load hail frequency severity metrics")
    def load_hail(self, subjects: Sequence[Tuple[str, str]], as_of: str) -> pd.DataFrame:
        return load_hail_frequency(subjects=list(subjects), as_of=as_of)

    @etl_task("load_snow", "Load snow load severity metrics")
    def load_snow(self, subjects: Sequence[Tuple[str, str]], as_of: str) -> pd.DataFrame:
        return load_snow_load(subjects=list(subjects), as_of=as_of)

    @etl_task("load_water_stress", "Load water stress metrics")
    def load_water(self, subjects: Sequence[Tuple[str, str]], as_of: str) -> pd.DataFrame:
        return load_water_stress(subjects=list(subjects), as_of=as_of)

    @etl_task("load_policy", "Load policy/regulatory risk metrics")
    def load_policy(self, subjects: Sequence[Tuple[str, str]], as_of: str) -> pd.DataFrame:
        return load_policy_risk_hazard(subjects=list(subjects), as_of=as_of)

    @etl_task("store_hazard_dataset", "Persist hazard dataset to data lake")
    def store(self, frame: pd.DataFrame, dataset: str, as_of: str) -> str:
        lake = DataLake()
        return lake.write(frame, dataset, as_of)


@timed_flow
@with_run_context
def refresh_hazard_metrics(
    subjects: Sequence[Tuple[str, str]] | None = None,
    as_of: str | None = None,
) -> dict[str, int]:
    flow = HazardMetricsFlow()
    subjects = tuple(subjects) if subjects else DEFAULT_SUBJECTS
    as_of_value = as_of or datetime.now().strftime("%Y-%m")
    flow.log_start(as_of=as_of_value)
    started = time.time()

    wildfire_df = flow.load_wildfire(subjects=subjects, as_of=as_of_value)
    hail_df = flow.load_hail(subjects=subjects, as_of=as_of_value)
    snow_df = flow.load_snow(subjects=subjects, as_of=as_of_value)
    water_df = flow.load_water(subjects=subjects, as_of=as_of_value)
    policy_df = flow.load_policy(subjects=subjects, as_of=as_of_value)

    flow.store(wildfire_df, dataset="hazard_wildfire", as_of=as_of_value)
    flow.store(hail_df, dataset="hazard_hail", as_of=as_of_value)
    flow.store(snow_df, dataset="hazard_snow", as_of=as_of_value)
    flow.store(water_df, dataset="hazard_water_stress", as_of=as_of_value)
    flow.store(policy_df, dataset="hazard_policy", as_of=as_of_value)

    duration = time.time() - started
    flow.log_complete(
        duration,
        as_of=as_of_value,
        wildfire_rows=len(wildfire_df),
        hail_rows=len(hail_df),
        snow_rows=len(snow_df),
        water_rows=len(water_df),
        policy_rows=len(policy_df),
    )
    return {
        "as_of": as_of_value,
        "wildfire_rows": len(wildfire_df),
        "hail_rows": len(hail_df),
        "snow_rows": len(snow_df),
        "water_rows": len(water_df),
        "policy_rows": len(policy_df),
    }


__all__ = ["HazardMetricsFlow", "refresh_hazard_metrics"]
