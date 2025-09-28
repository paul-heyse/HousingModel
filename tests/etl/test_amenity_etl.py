from __future__ import annotations

import pandas as pd
import pytest

from aker_core.etl.amenities import (
    load_membership_revenue,
    load_retention_signals,
    load_vendor_benchmarks,
)
from aker_data.amenities import AmenityBenchmarkStore


def setup_function() -> None:
    AmenityBenchmarkStore.instance().clear()


def teardown_function() -> None:
    AmenityBenchmarkStore.instance().clear()


def test_vendor_benchmarks_seed_store() -> None:
    df = load_vendor_benchmarks()
    store = AmenityBenchmarkStore.instance()
    assert not df.empty
    assert store.get("cowork_lounge") is not None


def test_membership_updates_benchmarks() -> None:
    load_vendor_benchmarks()
    df = load_membership_revenue(
        revenue_rows=[
            {"amenity_code": "cowork_lounge", "monthly_revenue": 1800.0, "utilization": 0.6},
            {"amenity_code": "cowork_lounge", "monthly_revenue": 1500.0, "utilization": 0.5},
        ]
    )
    store = AmenityBenchmarkStore.instance()
    benchmark = store.get("cowork_lounge")
    assert benchmark is not None
    assert benchmark.membership_revenue_monthly == pytest.approx(1650.0)
    assert isinstance(df, pd.DataFrame)


def test_retention_signals_merge() -> None:
    load_vendor_benchmarks()
    df = load_retention_signals(
        retention_rows=[{"amenity_code": "fitness_center", "retention_delta_bps": 175.0}]
    )
    store = AmenityBenchmarkStore.instance()
    benchmark = store.get("fitness_center")
    assert benchmark is not None
    assert benchmark.retention_delta_bps == 175.0
    assert "as_of" in df.columns
