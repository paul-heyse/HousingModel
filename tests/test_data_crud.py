from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aker_data.base import Base
from aker_data.models import Markets, PillarScores


def test_create_tables_and_crud_sqlite(tmp_path: Path) -> None:
    db_path: Path = tmp_path / "test.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        m = Markets(msa_id="BOI", name="Boise", pop=100, households=40, data_vintage="2025")
        session.add(m)
        session.flush()

        s = PillarScores(msa_id="BOI", supply_0_5=3.0)
        session.add(s)
        session.commit()

    with Session(engine) as session:
        markets = session.query(Markets).all()
        assert markets and markets[0].name == "Boise"

        scores = session.query(PillarScores).all()
        assert scores and scores[0].msa_id == "BOI"
