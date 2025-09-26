from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def _cfg(url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migration_stepping_and_idempotence(tmp_path: Path) -> None:
    url = f"sqlite+pysqlite:///{tmp_path / 'step.db'}"
    cfg = _cfg(url)

    command.upgrade(cfg, "0001_initial")
    command.upgrade(cfg, "head")
    # Idempotence
    command.upgrade(cfg, "head")

    command.downgrade(cfg, "0001_initial")
    command.downgrade(cfg, "base")
