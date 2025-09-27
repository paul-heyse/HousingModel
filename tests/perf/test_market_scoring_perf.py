from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from aker_core.markets.service import PillarScoreService
from aker_data.base import Base
from aker_data.models import (
    MarketJobs,
    MarketOutdoors,
    Markets,
    MarketSupply,
    MarketUrban,
    Runs,
)


@pytest.fixture()
def sqlite_engine(tmp_path: Path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'perf.db'}")

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, connection_record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _seed_market(session: Session, msa_id: str) -> None:
    session.add(Markets(msa_id=msa_id, name=f"Benchmark {msa_id}"))
    session.flush()
    session.add(
        MarketSupply(
            sba_id=f"{msa_id}-supply",
            msa_id=msa_id,
            permit_per_1k=3.0,
            vacancy_rate=5.0,
            tom_days=30.0,
            slope_pct=10.0,
            buffer_pct=12.0,
            height_idx=2.0,
            parking_idx=1.0,
        )
    )
    session.add(
        MarketJobs(
            sba_id=f"{msa_id}-jobs",
            msa_id=msa_id,
            tech_lq=1.3,
            health_lq=1.2,
            education_lq=1.1,
            manufacturing_lq=1.05,
            defense_lq=1.02,
            biotech_lq=1.1,
            tech_cagr_5yr=4.0,
            health_cagr_5yr=3.5,
            education_cagr_5yr=2.5,
            manufacturing_cagr_5yr=2.0,
            total_awards_per_100k=180.0,
            bfs_applications_per_100k=85.0,
            bfs_high_propensity_per_100k=60.0,
            startup_density=40.0,
            mig_25_44_per_1k=15.0,
            expansions_total_ct=15,
            expansions_total_jobs=1200,
            unemployment_rate=3.5,
            labor_participation_rate=64.0,
        )
    )
    session.add(
        MarketUrban(
            sba_id=f"{msa_id}-urban",
            msa_id=msa_id,
            walk_15_ct=28,
            bike_15_ct=20,
            k8_ct=15,
            transit_ct=18,
            urgent_ct=8,
            interx_km2=65.0,
            bikeway_conn_idx=58.0,
            retail_vac=7.0,
            retail_rent_qoq=1.5,
            daytime_pop_1mi=150000,
            lastmile_flag=bool(int(msa_id[-1]) % 2),
        )
    )
    session.add(
        MarketOutdoors(
            sba_id=f"{msa_id}-outdoors",
            msa_id=msa_id,
            min_trail_min=35,
            min_ski_bus_min=80,
            min_water_min=50,
            park_min=45,
            trail_mi_pc=2.0,
            public_land_30min_pct=55.0,
            pm25_var=4.5,
            smoke_days=6,
            hw_rail_prox_idx=68.0,
        )
    )


@pytest.mark.performance
def test_pillar_score_service_throughput(sqlite_engine, record_property):
    num_markets = 250
    with Session(sqlite_engine) as session:
        run = Runs(
            git_sha="perf-sha",
            config_hash="hash",
            config_json={},
            seed=321,
            started_at=datetime.now(timezone.utc),
            status="completed",
        )
        session.add(run)
        session.flush()

        for idx in range(num_markets):
            _seed_market(session, f"PERF{idx:04d}")
        session.commit()

    with Session(sqlite_engine) as session:
        service = PillarScoreService(session)
        start = perf_counter()
        results = service.refresh_many(as_of="2025-09", run_id=1)
        elapsed = perf_counter() - start

        record_property("markets_scored", len(results))
        record_property("elapsed_seconds", elapsed)

        assert len(results) == num_markets
        average_score = (
            sum(r.weighted_0_5 for r in results if r.weighted_0_5 is not None) / num_markets
        )
        assert math.isfinite(average_score)
        assert 0.0 <= average_score <= 5.0
