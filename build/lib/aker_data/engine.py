from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_postgis_engine(dsn: str) -> Engine:
    """Create a SQLAlchemy engine for PostgreSQL/PostGIS.

    dsn example: postgresql+psycopg://user:pass@host:5432/dbname
    """
    return create_engine(dsn, pool_pre_ping=True)


def create_sqlite_engine(path: str) -> Engine:
    """Create a SQLite engine for local dev/tests."""
    return create_engine(f"sqlite+pysqlite:///{path}")


def create_engine_from_url(url: str) -> Engine:
    if url.startswith("postgresql"):
        return create_postgis_engine(url)
    if url.startswith("sqlite"):
        return create_engine(url)
    return create_engine(url)
