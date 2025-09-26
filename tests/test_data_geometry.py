from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aker_data.base import Base
from aker_data.models import Assets


def test_insert_geometry_as_text_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "geom.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    wkt = "POINT(-116.214 43.618)"

    with Session(engine) as session:
        a = Assets(msa_id="BOI", geo=wkt, year_built=1990, units=10, product_type="garden")
        session.add(a)
        session.commit()

    with Session(engine) as session:
        row = session.query(Assets).first()
        assert row is not None
        assert isinstance(row.geo, str)
        assert "POINT" in row.geo
