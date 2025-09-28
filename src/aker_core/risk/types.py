"""Typed structures used by the risk engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping


@dataclass(frozen=True)
class RiskEntry:
    """Computed risk adjustment for a given subject and peril."""

    subject_type: str
    subject_id: str
    peril: str
    severity_idx: float
    multiplier: float
    deductible: Mapping[str, object]
    data_vintage: str
    source: str
    notes: str | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable dictionary representation."""

        payload: MutableMapping[str, object] = {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "peril": self.peril,
            "severity_idx": self.severity_idx,
            "multiplier": self.multiplier,
            "deductible": dict(self.deductible),
            "data_vintage": self.data_vintage,
            "source": self.source,
        }
        if self.notes:
            payload["notes"] = self.notes
        return dict(payload)


__all__ = ["RiskEntry"]
