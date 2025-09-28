from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import AssetFit


class AssetFitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, asset_id: int, msa_id: str, product_type: str | None, fit_score: float | None, flags: dict | None, inputs: dict | None, ruleset_version: str | None, context_label: str | None, run_id: int | None) -> AssetFit:
        record = AssetFit(
            asset_id=asset_id,
            msa_id=msa_id,
            product_type=product_type,
            fit_score=fit_score,
            flags=flags,
            inputs=inputs,
            ruleset_version=ruleset_version,
            context_label=context_label,
            run_id=run_id,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_latest(self, *, asset_id: int) -> Optional[AssetFit]:
        stmt = select(AssetFit).where(AssetFit.asset_id == asset_id).order_by(AssetFit.evaluated_at.desc())
        return self.session.execute(stmt).scalars().first()
