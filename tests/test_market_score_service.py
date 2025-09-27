from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from aker_core.markets.service import PillarScoreService
from aker_data.base import Base
from aker_data.models import (
    MarketJobs,
    MarketOutdoors,
    Markets,
    MarketSupply,
    MarketUrban,
    PillarScores,
    Runs,
)


@pytest.fixture()
def sqlite_engine(tmp_path: Path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'service.db'}")

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, connection_record):  # pragma: no cover - sqlite hook
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_pillar_score_service_refresh(sqlite_engine) -> None:
    msa_id = "555555555555"
    with Session(sqlite_engine) as session:
        run = Runs(
            git_sha="service-sha",
            config_hash="hash",
            config_json={},
            seed=123,
            started_at=datetime.now(timezone.utc),
            status="completed",
        )
        session.add(run)
        session.flush()

        market = Markets(msa_id=msa_id, name="Service Market")
        session.add(market)
        session.flush()

        session.add_all(
            [
                MarketSupply(
                    sba_id=f"{msa_id}-001",
                    msa_id=msa_id,
                    permit_per_1k=3.0,
                    vacancy_rate=4.5,
                    tom_days=28.0,
                ),
                MarketJobs(
                    sba_id=f"{msa_id}-001",
                    msa_id=msa_id,
                    tech_cagr_5yr=5.0,
                    tech_lq=1.4,
                    total_awards_per_100k=220.0,
                    bfs_applications_per_100k=80.0,
                ),
                MarketUrban(
                    sba_id=f"{msa_id}-001",
                    msa_id=msa_id,
                    walk_15_ct=30,
                    bike_15_ct=20,
                    interx_km2=70.0,
                    retail_vac=6.0,
                    retail_rent_qoq=2.0,
                ),
                MarketOutdoors(
                    sba_id=f"{msa_id}-001",
                    msa_id=msa_id,
                    min_trail_min=25,
                    trail_mi_pc=2.2,
                    public_land_30min_pct=55.0,
                    smoke_days=3,
                ),
            ]
        )
        session.commit()

    with Session(sqlite_engine) as session:
        service = PillarScoreService(session)
        assert session.get(Markets, msa_id) is not None
        result = service.refresh_one(msa_id, as_of="2025-09", run_id=1)
        session.commit()

        snapshot_path = Path(__file__).parent / "data" / "market_score_snapshot.json"
        expected = json.loads(snapshot_path.read_text())

        assert result is not None
        for key, expected_value in expected["pillar_scores"].items():
            actual = getattr(result, key)
            assert math.isclose(actual, expected_value, rel_tol=1e-9, abs_tol=1e-9)

        assert result.weights == expected["weights"]
        assert str(result.score_as_of) == expected["score_as_of"]

    with Session(sqlite_engine) as session:
        record = session.scalars(select(PillarScores).where(PillarScores.msa_id == msa_id)).one()
        assert record.supply_0_5 is not None
        assert record.jobs_0_5 is not None
        assert record.urban_0_5 is not None
        assert record.outdoor_0_5 is not None
        if result is not None:
            assert record.weighted_0_5 is not None
            assert record.weighted_0_100 is not None
            assert record.weights is not None
            assert record.score_as_of is not None
