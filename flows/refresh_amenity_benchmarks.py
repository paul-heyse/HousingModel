"""Prefect flow for refreshing amenity ROI benchmark datasets."""

from __future__ import annotations

import time
from datetime import datetime

import pandas as pd

from aker_data.amenities import AmenityBenchmarkStore
from aker_data.lake import DataLake

from aker_core.etl.amenities import (
    load_membership_revenue,
    load_retention_signals,
    load_vendor_benchmarks,
)

from .base import ETLFlow, etl_task, timed_flow, with_run_context


class AmenityBenchmarkFlow(ETLFlow):
    def __init__(self) -> None:
        super().__init__(
            "refresh_amenity_benchmarks",
            "Refresh amenity ROI benchmark datasets (vendor costs, membership revenue, retention signals).",
        )

    @etl_task("load_vendor", "Load vendor amenity benchmarks")
    def ingest_vendor(self, as_of: str) -> pd.DataFrame:
        return load_vendor_benchmarks(as_of=as_of)

    @etl_task("load_membership", "Load amenity membership revenue data")
    def ingest_membership(self, as_of: str) -> pd.DataFrame:
        return load_membership_revenue(as_of=as_of)

    @etl_task("load_retention", "Load amenity retention deltas")
    def ingest_retention(self, as_of: str) -> pd.DataFrame:
        return load_retention_signals(as_of=as_of)

    @etl_task("store_amenity_dataset", "Persist amenity benchmark dataset to data lake")
    def store(self, df: pd.DataFrame, dataset: str, as_of: str) -> str:
        lake = DataLake()
        return lake.write(df, dataset, as_of)


@timed_flow
@with_run_context
def refresh_amenity_benchmarks(as_of: str | None = None) -> dict[str, int]:
    flow = AmenityBenchmarkFlow()
    as_of_value = as_of or datetime.now().strftime("%Y-%m")
    flow.log_start(as_of=as_of_value)
    started = time.time()

    store = AmenityBenchmarkStore.instance()
    store.clear()

    vendor_df = flow.ingest_vendor(as_of=as_of_value)
    membership_df = flow.ingest_membership(as_of=as_of_value)
    retention_df = flow.ingest_retention(as_of=as_of_value)

    flow.store(vendor_df, dataset="amenity_vendor_benchmarks", as_of=as_of_value)
    flow.store(membership_df, dataset="amenity_membership_revenue", as_of=as_of_value)
    flow.store(retention_df, dataset="amenity_retention_signals", as_of=as_of_value)

    duration = time.time() - started
    flow.log_complete(
        duration,
        as_of=as_of_value,
        vendor_rows=len(vendor_df),
        membership_rows=len(membership_df),
        retention_rows=len(retention_df),
    )

    return {
        "as_of": as_of_value,
        "vendor_rows": len(vendor_df),
        "membership_rows": len(membership_df),
        "retention_rows": len(retention_df),
    }


__all__ = ["AmenityBenchmarkFlow", "refresh_amenity_benchmarks"]
