from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aker_data.base import Base
from aker_data.materialized import MaterializedTableManager
from aker_data.models import (
    AssetPerformance,
    Assets,
    MarketAnalytics,
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
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'materialized.db'}")

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, connection_record):  # pragma: no cover - sqlite hook
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


def _seed_base_data(session: Session, *, include_composite: bool = True) -> int:
    run = Runs(
        git_sha="abc123def4567890",
        config_hash="hash",
        config_json={},
        seed=42,
        started_at=datetime.now(timezone.utc),
        status="completed",
    )
    session.add(run)
    session.flush()

    market = Markets(
        msa_id="123456789012",
        name="Test Market",
        pop=100_000,
        households=40_000,
    )
    session.add(market)
    session.flush()

    session.add_all(
        [
            MarketSupply(
                sba_id="123456789012-001",
                msa_id=market.msa_id,
                permit_per_1k=2.5,
                vacancy_rate=5.0,
            ),
            MarketJobs(
                sba_id="123456789012-001",
                msa_id=market.msa_id,
                tech_cagr_5yr=4.5,
            ),
            MarketUrban(
                sba_id="123456789012-001",
                msa_id=market.msa_id,
                walk_15_ct=25,
            ),
            MarketOutdoors(
                sba_id="123456789012-001",
                msa_id=market.msa_id,
                trail_mi_pc=1.5,
            ),
        ]
    )

    pillar_kwargs = dict(
        msa_id=market.msa_id,
        supply_0_5=4.0,
        jobs_0_5=3.5,
        urban_0_5=3.0,
        outdoor_0_5=2.5,
        run_id=run.run_id,
    )
    if include_composite:
        pillar_kwargs.update(
            weighted_0_5=3.5,
            weighted_0_100=70.0,
            weights={"supply": 0.3, "jobs": 0.3, "urban": 0.2, "outdoor": 0.2},
            score_as_of=datetime.now(timezone.utc).date(),
        )

    session.add(PillarScores(**pillar_kwargs))

    session.add(
        Assets(
            msa_id=market.msa_id,
            units=120,
            year_built=2010,
        )
    )

    session.commit()
    return run.run_id


def test_materialized_refresh_populates_tables_and_views(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        run_id = _seed_base_data(session)

    manager = MaterializedTableManager(sqlite_engine, run_id=run_id)
    market_result = manager.refresh_market_analytics(period="2025-09")
    asset_result = manager.refresh_asset_performance(period="2025-09")

    assert market_result.rows == 1
    assert asset_result.rows == 1
    assert market_result.validation is not None and market_result.validation.success is True
    assert asset_result.validation is not None and asset_result.validation.success is True

    with Session(sqlite_engine) as session:
        market_row = session.scalars(select(MarketAnalytics)).one()
        assert market_row.msa_id == "123456789012"
        assert market_row.composite_score is not None

        asset_row = session.scalars(select(AssetPerformance)).one()
        assert asset_row.asset_id is not None
        assert asset_row.rank_in_market == 1

    with sqlite_engine.connect() as conn:
        view_row = conn.execute(
            text("SELECT market_name, composite_score FROM market_supply_joined WHERE msa_id=:msa"),
            {"msa": "123456789012"},
        ).fetchone()
        assert view_row is not None

        scoring_row = conn.execute(
            text("SELECT asset_id, score FROM asset_scoring_joined WHERE msa_id=:msa"),
            {"msa": "123456789012"},
        ).fetchone()
        assert scoring_row is not None


def test_foreign_key_constraints_enforced(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        session.add(
            Markets(
                msa_id="999999999999",
                name="Other Market",
            )
        )
        session.commit()

    with pytest.raises(IntegrityError):
        session.add(
            Assets(
                msa_id="does-not-exist",
                units=10,
            )
        )
        session.commit()


def test_refresh_market_analytics_composes_missing_scores(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        run_id = _seed_base_data(session, include_composite=False)

    manager = MaterializedTableManager(sqlite_engine, run_id=run_id)
    result = manager.refresh_market_analytics(period="2025-10")

    assert result.rows == 1

    with Session(sqlite_engine) as session:
        pillar = session.scalars(select(PillarScores)).one()
        assert pillar.weighted_0_5 is not None
        assert pillar.weighted_0_100 is not None
        assert pillar.score_as_of == datetime.strptime("2025-10", "%Y-%m").date().replace(day=1)
