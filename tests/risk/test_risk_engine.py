from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aker_core.database.risk import RiskRepository
from aker_core.risk import build_risk_table
from aker_core.risk import compute as compute_risk_entry
from aker_core.risk.engine import RiskEngine
from aker_data.base import Base
from aker_data.hazards import HazardDataStore, HazardRecord


@pytest.fixture()
def sqlite_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'risk.db'}")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture()
def hazard_store() -> HazardDataStore:
    store = HazardDataStore.instance()
    store.clear()
    yield store
    store.clear()


def test_compute_persists_profile(sqlite_session: Session, hazard_store: HazardDataStore) -> None:
    hazard_store.ingest(
        "wildfire",
        [
            HazardRecord(
                subject_type="market",
                subject_id="MSAX01",
                severity_idx=72.5,
                data_vintage="2025-09",
                source="Test WUI",
                metadata={"note": "High WUI exposure"},
            )
        ],
    )

    entry = compute_risk_entry(
        {"subject_type": "market", "subject_id": "MSAX01"},
        "wildfire",
        session=sqlite_session,
        run_id=42,
        hazard_store=hazard_store,
    )

    assert 0.9 <= entry.multiplier <= 1.1
    repo = RiskRepository(sqlite_session)
    stored = repo.fetch_profile("market", "MSAX01", "wildfire")
    assert stored is not None
    assert stored.run_id == 42
    assert stored.severity_idx == pytest.approx(entry.severity_idx)
    assert stored.multiplier == pytest.approx(entry.multiplier)
    assert stored.deductible["recommended_deductible_bps"] >= 150


def test_monotonic_multiplier(hazard_store: HazardDataStore) -> None:
    hazard_store.ingest(
        "hail",
        [
            HazardRecord("market", "LOW", 10.0, "2025-09", "Test", {}),
            HazardRecord("market", "HIGH", 85.0, "2025-09", "Test", {}),
        ],
    )

    low = compute_risk_entry("LOW", "hail", hazard_store=hazard_store)
    high = compute_risk_entry("HIGH", "hail", hazard_store=hazard_store)

    assert low.multiplier > high.multiplier
    assert 0.9 <= high.multiplier <= 1.1
    assert 0.9 <= low.multiplier <= 1.1


def test_apply_to_underwrite_combines_multipliers(
    sqlite_session: Session, hazard_store: HazardDataStore
) -> None:
    hazard_store.ingest(
        "wildfire",
        [HazardRecord("market", "MSA001", 20.0, "2025-09", "Test", {})],
    )
    hazard_store.ingest(
        "policy_risk",
        [HazardRecord("market", "MSA001", 65.0, "2025-09", "Test", {})],
    )

    engine = RiskEngine(sqlite_session, hazard_store=hazard_store)
    entry_a = engine.compute("MSA001", "wildfire")
    entry_b = engine.compute("MSA001", "policy_risk")

    base_payload = {"exit_cap_rate": 0.055, "contingency_pct": 0.08}
    result = engine.apply_to_underwrite(base_payload, [entry_a, entry_b])

    expected_multiplier = pytest.approx(entry_a.multiplier * entry_b.multiplier)
    assert result["risk_multiplier"] == expected_multiplier
    assert "risk_adjusted_exit_cap_rate" in result
    assert result["risk_adjustments"][0]["peril"] == "wildfire"
    # Ensure input payload remains unchanged
    assert base_payload["exit_cap_rate"] == 0.055


def test_build_risk_table_returns_clean_output(hazard_store: HazardDataStore) -> None:
    hazard_store.ingest(
        "water_stress",
        [HazardRecord("market", "MSA777", 55.0, "2025-09", "Test", {"note": "Moderate drought"})],
    )
    entry = compute_risk_entry("MSA777", "water_stress", hazard_store=hazard_store)
    table = build_risk_table([entry])
    assert table and table[0]["Peril"] == "Water Stress"
    assert table[0]["SeverityIdx"] == entry.severity_idx
    assert table[0]["RecommendedDeductibleBps"] == entry.deductible["recommended_deductible_bps"]
    assert "Notes" in table[0]
