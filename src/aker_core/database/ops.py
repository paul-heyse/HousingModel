from __future__ import annotations

from sqlalchemy.orm import Session

from aker_data.models_extra import OpsModel


class OpsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_index(self, *, asset_id: int, nps: int | None, reputation_idx: float | None, cadence_plan: str | None = None, concession_days_saved: int | None = None) -> OpsModel:
        row = self.session.get(OpsModel, asset_id)
        if row is None:
            row = OpsModel(asset_id=asset_id)
            self.session.add(row)
        row.nps = nps
        row.reputation_idx = reputation_idx
        row.cadence_plan = cadence_plan
        row.concession_days_saved = concession_days_saved
        self.session.flush()
        return row
