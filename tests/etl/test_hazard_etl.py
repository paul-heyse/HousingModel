from __future__ import annotations

import pandas as pd
import pytest

from aker_core.etl.hazards import load_policy_risk, load_water_stress, load_wildfire_wui
from aker_data.hazards import HazardDataStore


@pytest.fixture()
def hazard_store() -> HazardDataStore:
    store = HazardDataStore.instance()
    store.clear()
    yield store
    store.clear()


def test_wildfire_etl_populates_store(hazard_store: HazardDataStore) -> None:
    df = load_wildfire_wui(subjects=["MSA100", ("asset", "A-1")], hazard_store=hazard_store)
    assert isinstance(df, pd.DataFrame)
    assert set(["peril", "subject_type", "subject_id", "severity_idx"]).issubset(df.columns)
    record = hazard_store.get("wildfire", "market", "MSA100")
    assert record is not None
    assert 0 <= record.severity_idx <= 100


def test_policy_risk_metadata_flags(hazard_store: HazardDataStore) -> None:
    df = load_policy_risk(subjects=["MSA200"], hazard_store=hazard_store, as_of="2025-10")
    assert df.iloc[0]["data_vintage"] == "2025-10"
    record = hazard_store.get("policy_risk", "market", "MSA200")
    assert record is not None
    assert "insurance_regime" in record.metadata


def test_water_stress_metadata_contains_flags(hazard_store: HazardDataStore) -> None:
    load_water_stress(subjects=["MSA555"], hazard_store=hazard_store)
    record = hazard_store.get("water_stress", "market", "MSA555")
    assert record is not None
    assert "tap_moratorium_flag" in record.metadata
