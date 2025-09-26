from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_migration_upgrade_downgrade_sqlite(tmp_path: Path) -> None:
    db_path: Path = tmp_path / "mig.db"
    url = f"sqlite+pysqlite:///{db_path}"
    cfg = _alembic_cfg(url)

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert "markets" in tables and "pillar_scores" in tables

    command.downgrade(cfg, "base")

    insp = inspect(engine)
    tables_after = set(insp.get_table_names())
    assert "markets" not in tables_after and "pillar_scores" not in tables_after
