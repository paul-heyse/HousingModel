from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from aker_core.amenities import AmenityEngine, AmenityInput, build_amenity_table
from aker_core.amenities.engine import evaluate as evaluate_amenity
from aker_data.amenities import AmenityBenchmarkStore
from aker_data.base import Base
from aker_data.models import AmenityProgram, Assets


@pytest.fixture()
def sqlite_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'amenities.db'}")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            # Seed asset for evaluation
            session.add(Assets(asset_id=1, msa_id="TESTMSA", units=150))
            session.commit()
            yield session
    finally:
        engine.dispose()


@pytest.fixture(autouse=True)
def clear_benchmarks() -> None:
    store = AmenityBenchmarkStore.instance()
    store.clear()
    yield
    store.clear()


def test_positive_premium_and_retention_increase_noi(sqlite_session: Session) -> None:
    engine = AmenityEngine(sqlite_session)
    amenity = AmenityInput(amenity_code="cowork_lounge")
    result = engine.evaluate(asset_id=1, amenities=[amenity])

    assert result.impacts.total_noi_delta_annual > 0
    detail = result.details[0]
    assert detail.payback_months is not None
    count_stmt = select(func.count()).select_from(AmenityProgram).where(
        AmenityProgram.asset_id == 1, AmenityProgram.amenity_code == "cowork_lounge"
    )
    stored = sqlite_session.execute(count_stmt).scalar_one()
    assert stored == 1


def test_custom_inputs_override_benchmarks(sqlite_session: Session) -> None:
    engine = AmenityEngine(sqlite_session)
    amenity = AmenityInput(
        amenity_code="fitness_center",
        rent_premium_per_unit=120.0,
        membership_revenue_monthly=0.0,
        capex=100000.0,
        opex_monthly=200.0,
    )
    result = engine.evaluate(asset_id=1, amenities=[amenity])
    detail = result.details[0]
    assert detail.rent_premium_per_unit == 120.0
    assert detail.payback_months is not None


def test_module_level_evaluate(sqlite_session: Session) -> None:
    result = evaluate_amenity(
        session=sqlite_session,
        asset_id=1,
        amenities=[AmenityInput(amenity_code="pet_spa")],
    )
    assert result.impacts.total_capex >= 0


def test_build_amenity_table(sqlite_session: Session) -> None:
    engine = AmenityEngine(sqlite_session)
    result = engine.evaluate(
        asset_id=1,
        amenities=[AmenityInput(amenity_code="cowork_lounge"), AmenityInput(amenity_code="fitness_center")],
    )
    table = build_amenity_table(result.details)
    assert len(table) == 2
    assert table[0]["Amenity"]


def test_negative_benefit_results_in_no_payback(sqlite_session: Session) -> None:
    engine = AmenityEngine(sqlite_session)
    amenity = AmenityInput(
        amenity_code="smart_access",
        rent_premium_per_unit=0.0,
        membership_revenue_monthly=0.0,
        capex=50000.0,
        opex_monthly=1000.0,
        retention_delta_bps=0.0,
    )
    result = engine.evaluate(asset_id=1, amenities=[amenity])
    detail = result.details[0]
    assert detail.payback_months is None
    assert detail.noi_delta_annual <= 0
