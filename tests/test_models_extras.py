from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aker_data.base import Base
from aker_data.models_extra import AmenityProgram, AssetFit, DealArchetype, OpsModel, RiskProfile


def test_crud_extras_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "extras.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        af = AssetFit(asset_id=1, product_type="garden", fit_score=72.5)
        da = DealArchetype(name="light value-add", cost=8000.0, payback_mo=36)
        ap = AmenityProgram(asset_id=1, amenity="dog wash", capex=2500.0)
        rp = RiskProfile(peril="hail", multiplier=1.05)
        om = OpsModel(asset_id=1, nps=45)
        session.add_all([af, da, ap, rp, om])
        session.commit()

    with Session(engine) as session:
        af_loaded = session.get(AssetFit, 1)
        assert af_loaded is not None and af_loaded.fit_score == 72.5
        da_loaded = session.query(DealArchetype).first()
        assert da_loaded is not None and da_loaded.name.startswith("light")
        ap_loaded = session.get(AmenityProgram, 1)
        assert ap_loaded is not None and ap_loaded.amenity == "dog wash"
        rp_loaded = session.query(RiskProfile).first()
        assert rp_loaded is not None and rp_loaded.peril == "hail"
        om_loaded = session.get(OpsModel, 1)
        assert om_loaded is not None and om_loaded.nps == 45
