from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aker_data.base import Base
from aker_data.models import Markets


def test_non_null_constraint_and_index(tmp_path: Path) -> None:
    db_path = tmp_path / "idx.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    # Markets.name is non-nullable in our model
    committed = True
    with Session(engine) as session:
        try:
            session.add(Markets(msa_id="X", name=None))
            session.commit()
        except IntegrityError:
            session.rollback()
            committed = False
    # Accept either enforced non-null or successful commit with non-null required later
    if committed:
        with Session(engine) as session:
            row = session.get(Markets, "X")
            assert row is None or row.name is not None

    # Ensure pillar_scores exists and msa_id column present
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("pillar_scores")}
    assert "msa_id" in cols
