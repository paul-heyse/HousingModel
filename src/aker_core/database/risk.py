"""Persistence helpers for risk profile computations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import RiskProfile

from ..risk.types import RiskEntry


class RiskRepository:
    """Read/write access to `risk_profile` records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------
    def upsert_profile(
        self,
        entry: RiskEntry,
        *,
        run_id: Optional[int] = None,
        calculation_method: Optional[str] = None,
    ) -> RiskProfile:
        """Insert or update the stored risk profile for the subject/peril."""

        stmt = select(RiskProfile).where(
            RiskProfile.subject_type == entry.subject_type,
            RiskProfile.subject_id == entry.subject_id,
            RiskProfile.peril == entry.peril,
        )
        record = self.session.execute(stmt).scalar_one_or_none()

        payload = {
            "severity_idx": entry.severity_idx,
            "multiplier": entry.multiplier,
            "deductible": dict(entry.deductible),
            "data_vintage": entry.data_vintage,
            "source": entry.source,
            "notes": entry.notes,
        }
        if run_id is not None:
            payload["run_id"] = run_id
        if calculation_method is not None:
            payload["calculation_method"] = calculation_method

        if record is None:
            record = RiskProfile(
                subject_type=entry.subject_type,
                subject_id=entry.subject_id,
                peril=entry.peril,
                **payload,
            )
            self.session.add(record)
        else:
            for key, value in payload.items():
                setattr(record, key, value)

        self.session.flush()
        return record

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------
    def fetch_profile(
        self, subject_type: str, subject_id: str, peril: str
    ) -> Optional[RiskProfile]:
        """Retrieve a stored risk profile entry if present."""

        stmt = select(RiskProfile).where(
            RiskProfile.subject_type == subject_type,
            RiskProfile.subject_id == subject_id,
            RiskProfile.peril == peril,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_subject_profiles(self, subject_type: str, subject_id: str) -> list[RiskProfile]:
        """Return all risk profile entries for a subject."""

        stmt = select(RiskProfile).where(
            RiskProfile.subject_type == subject_type,
            RiskProfile.subject_id == subject_id,
        )
        result = self.session.execute(stmt)
        return list(result.scalars())


__all__ = ["RiskRepository"]
