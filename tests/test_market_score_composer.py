from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from aker_core.markets.composer import MarketPillarScores, score, score_many
from aker_data.base import Base
from aker_data.models import Markets, PillarScores, Runs


@pytest.fixture()
def sqlite_engine(tmp_path: Path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'composer.db'}")

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_connection, connection_record):  # pragma: no cover - SQLite hook
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _seed_scores(
    session: Session,
    *,
    msa_id: str | None = None,
    supply: float = 3.4,
    jobs: float = 3.0,
    urban: float = 2.8,
    outdoor: float = 3.2,
) -> PillarScores:
    resolved_msa = msa_id or f"{uuid4().hex[:12].upper()}"
    market = Markets(msa_id=resolved_msa, name="Testopia")
    session.add(market)
    session.flush()

    scores = PillarScores(
        msa_id=market.msa_id,
        supply_0_5=supply,
        jobs_0_5=jobs,
        urban_0_5=urban,
        outdoor_0_5=outdoor,
    )
    session.add(scores)
    session.flush()
    return scores


def _seed_run(session: Session) -> Runs:
    run = Runs(
        git_sha="test-sha",
        config_hash="test-config",
        config_json={},
        seed=1,
        started_at=datetime.now(timezone.utc),
        status="completed",
    )
    session.add(run)
    session.flush()
    return run


def test_default_weights_composer(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        record = _seed_scores(session, msa_id="999999999999")

        run = _seed_run(session)
        result = score(session=session, msa_id=record.msa_id, as_of="2025-09", run_id=run.run_id)
        assert isinstance(result, MarketPillarScores)
        expected_default = (
            record.supply_0_5 * 0.3
            + record.jobs_0_5 * 0.3
            + record.urban_0_5 * 0.2
            + record.outdoor_0_5 * 0.2
        )
        assert result.weighted_0_5 == pytest.approx(expected_default, rel=1e-6)
        assert result.weighted_0_100 == pytest.approx(result.weighted_0_5 * 20.0, rel=1e-6)
        assert result.score_as_of == date(2025, 9, 1)
        assert result.run_id == run.run_id
        assert set(result.weights.keys()) == {"supply", "jobs", "urban", "outdoor"}

        session.refresh(record)
        assert record.weighted_0_5 == pytest.approx(result.weighted_0_5, rel=1e-6)
        assert record.weighted_0_100 == pytest.approx(result.weighted_0_100, rel=1e-6)
        assert record.score_as_of == date(2025, 9, 1)
        assert record.run_id == run.run_id
        assert record.weights is not None
        for key, value in result.weights.items():
            assert key in record.weights
            assert pytest.approx(record.weights[key], rel=1e-9) == value
        assert record.run_id == run.run_id


def test_weight_override_normalised(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        record = _seed_scores(
            session,
            msa_id="888888888887",
            supply=4.0,
            jobs=2.0,
            urban=3.0,
            outdoor=1.0,
        )

        overrides = {"supply": 0.1, "jobs": 0.6, "urban": 0.2, "outdoor": 0.1}
        run = _seed_run(session)
        result = score(session=session, msa_id=record.msa_id, weights=overrides, run_id=run.run_id)

        assert sum(result.weights.values()) == pytest.approx(1.0, rel=1e-9)
        assert result.weights["jobs"] == pytest.approx(0.6, rel=1e-9)
        assert result.weights["supply"] == pytest.approx(0.1, rel=1e-9)

        expected = (
            record.supply_0_5 * overrides["supply"]
            + record.jobs_0_5 * overrides["jobs"]
            + record.urban_0_5 * overrides["urban"]
            + record.outdoor_0_5 * overrides["outdoor"]
        )
        assert result.weighted_0_5 == pytest.approx(expected, rel=1e-6)

        session.refresh(record)
        assert record.weights is not None
        for key, value in result.weights.items():
            assert key in record.weights
            assert pytest.approx(record.weights[key], rel=1e-9) == value
        assert record.run_id == run.run_id


def test_missing_pillar_raises(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        market = Markets(msa_id="888888888888", name="Missing Pillar")
        session.add(market)
        session.flush()
        session.add(
            PillarScores(
                msa_id=market.msa_id,
                supply_0_5=4.0,
                jobs_0_5=None,
                urban_0_5=3.0,
                outdoor_0_5=2.0,
            )
        )
        session.flush()

        with pytest.raises(ValueError, match="Missing pillar scores"):
            score(session=session, msa_id=market.msa_id)


def test_score_many_with_default_population(sqlite_engine) -> None:
    with Session(sqlite_engine) as session:
        first = _seed_scores(session, supply=3.0, jobs=3.5, urban=3.2, outdoor=2.8)
        second = _seed_scores(session, supply=4.1, jobs=2.9, urban=3.3, outdoor=3.0)

        results = score_many(session=session, as_of="2025-08")
        assert len(results) == 2
        msas = {r.msa_id for r in results}
        assert msas == {first.msa_id, second.msa_id}

        session.refresh(first)
        session.refresh(second)
        assert first.score_as_of is not None
        assert second.score_as_of is not None
