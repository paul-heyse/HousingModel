from __future__ import annotations

from sqlalchemy.dialects.postgresql.psycopg import dialect as pg_dialect
from sqlalchemy.dialects.sqlite.pysqlite import dialect as sqlite_dialect
from sqlalchemy.engine import Engine

from aker_data.engine import create_engine_from_url
from aker_data.types import GeoType


def test_geotype_dialect_impl() -> None:
    g = GeoType("POINT", 4326)
    assert g.load_dialect_impl(pg_dialect()) is not None
    # For SQLite, fallback should be Text()
    assert g.load_dialect_impl(sqlite_dialect()).python_type is str


def test_engine_helper_dispatch() -> None:
    eng: Engine = create_engine_from_url("sqlite+pysqlite:///./local.db")
    assert "sqlite" in str(eng.url)
    assert "sqlite" in str(create_engine_from_url("sqlite+pysqlite:///./local.db").url)
