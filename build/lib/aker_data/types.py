from __future__ import annotations

from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import TypeDecorator


class GeoType(TypeDecorator):
    """Dialect-aware geometry type.

    Uses PostGIS Geometry on PostgreSQL and falls back to TEXT elsewhere (e.g., SQLite/SpatiaLite dev).
    Stores WKT/WKB-compatible payloads when not on PostGIS.
    """

    cache_ok = True
    impl = Text

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326) -> None:
        super().__init__()
        self.geometry_type = geometry_type
        self.srid = srid

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "postgresql":
            return Geometry(geometry_type=self.geometry_type, srid=self.srid)
        return Text()

    def process_bind_param(
        self, value: Any, dialect: Dialect
    ) -> Any:  # pragma: no cover - passthrough
        return value

    def process_result_value(
        self, value: Any, dialect: Dialect
    ) -> Any:  # pragma: no cover - passthrough
        return value


JsonType = JSONB
