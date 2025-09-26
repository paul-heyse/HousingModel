from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aker_core.config import Settings, reset_settings_cache
from aker_core.run import RunContext
from aker_data.base import Base
from aker_data.models import Lineage, PillarScores, Runs


@pytest.fixture
def session_factory(tmp_path, monkeypatch):
    monkeypatch.setenv("AKER_POSTGIS_DSN", "postgresql://example.com/db")
    reset_settings_cache()
    db_path = tmp_path / "run.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    yield factory
    engine.dispose()
    reset_settings_cache()


def _output_hash(value: float) -> str:
    return hashlib.sha256(f"{value:.12f}".encode()).hexdigest()


def test_run_context_persists_metadata_and_lineage(session_factory) -> None:
    settings = Settings()
    fetched_at = datetime.now(timezone.utc)

    with RunContext(session_factory, settings=settings, git_sha="abc123") as run:
        value = run.rng.random()
        expected_hash = _output_hash(value)
        run.session.add(PillarScores(msa_id="BOI", supply_0_5=value, run_id=run.id))
        run.log_lineage(
            table="markets",
            source="census",
            url="https://census.gov",
            fetched_at=fetched_at,
            hash_value="dataset-hash",
        )
        run.set_output_hash(expected_hash)

    with session_factory() as session:  # type: Session
        stored_run = session.query(Runs).one()
        assert stored_run.git_sha == "abc123"
        assert stored_run.status == "completed"
        assert stored_run.finished_at is not None
        assert stored_run.output_hash == expected_hash
        assert stored_run.config_hash
        assert stored_run.seed == int(stored_run.config_hash[:16], 16) % (2**32)

        lineage_row = session.query(Lineage).one()
        assert lineage_row.run_id == stored_run.run_id
        assert lineage_row.source_url == "https://census.gov"
        assert lineage_row.hash == "dataset-hash"


def test_run_context_deterministic_rerun(session_factory) -> None:
    settings = Settings()

    def execute_pipeline() -> str:
        with RunContext(session_factory, settings=settings, git_sha="abc123") as run:
            value = run.rng.random()
            run.session.add(PillarScores(msa_id=f"{run.id}-msa", supply_0_5=value, run_id=run.id))
            hash_value = _output_hash(value)
            run.set_output_hash(hash_value)
        return hash_value

    first_hash = execute_pipeline()
    second_hash = execute_pipeline()

    assert first_hash == second_hash

    with session_factory() as session:
        hashes = [row.output_hash for row in session.query(Runs).order_by(Runs.run_id)]
    assert hashes == [first_hash, second_hash]


def test_log_lineage_requires_active_context(session_factory) -> None:
    settings = Settings()
    context = RunContext(session_factory, settings=settings, git_sha="abc123")

    with pytest.raises(RuntimeError):
        context.log_lineage(
            table="markets",
            source="census",
            url="https://example.com",
            fetched_at=datetime.now(timezone.utc),
            hash_value="hash",
        )


def test_run_context_failure_rolls_back(session_factory) -> None:
    settings = Settings()

    with pytest.raises(RuntimeError):
        with RunContext(session_factory, settings=settings, git_sha="abc123") as run:
            run.session.add(PillarScores(msa_id="ERR", supply_0_5=1.0, run_id=run.id))
            raise RuntimeError("pipeline failure")

    with session_factory() as session:
        stored_run = session.query(Runs).one()
        assert stored_run.status == "failed"
        assert stored_run.finished_at is not None
        # record should not persist because data session rolled back
        assert session.query(PillarScores).count() == 0


def test_run_context_seed_override(session_factory) -> None:
    settings = Settings()

    with RunContext(session_factory, settings=settings, git_sha="abc123", seed=1234) as run:
        assert run.seed == 1234
        assert run.rng.random() == pytest.approx(0.9664535356921388)


def test_run_context_session_contract(session_factory) -> None:
    context = RunContext(session_factory, settings=Settings(), git_sha="abc123")
    with pytest.raises(RuntimeError):
        context.session
    with pytest.raises(RuntimeError):
        context.set_output_hash("abc")
