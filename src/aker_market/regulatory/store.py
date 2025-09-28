"""Persistence helpers for regulatory friction encodings."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd


@dataclass
class RegulatoryStore:
    """In-memory persistence for regulatory friction encodings."""

    _frame: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=[
                "msa_id",
                "iz_flag",
                "review_flag",
                "height_idx",
                "parking_idx",
                "water_moratorium_flag",
                "provenance",
            ]
        )
    )

    def upsert(self, msa_id: str, encoding: Dict[str, object], provenance: Optional[Dict[str, str]] = None) -> None:
        """Insert or update a regulatory encoding for the given MSA."""

        if not msa_id:
            raise ValueError("msa_id is required for persistence")

        payload = {
            "msa_id": msa_id,
            "iz_flag": bool(encoding.get("iz_flag", False)),
            "review_flag": bool(encoding.get("review_flag", False)),
            "height_idx": int(encoding.get("height_idx", 0)),
            "parking_idx": int(encoding.get("parking_idx", 0)),
            "water_moratorium_flag": bool(encoding.get("water_moratorium_flag", False)),
            "provenance": json.dumps(provenance or encoding.get("provenance", {})),
        }

        frame = self._frame
        exists = frame["msa_id"] == msa_id
        if exists.any():
            self._frame.loc[exists, :] = payload
        else:
            self._frame = pd.concat([frame, pd.DataFrame([payload])], ignore_index=True)

    def get(self, msa_id: str) -> Optional[pd.Series]:
        """Return the stored encoding for an MSA if present."""

        matches = self._frame[self._frame["msa_id"] == msa_id]
        if matches.empty:
            return None
        return matches.iloc[0]

    def to_frame(self) -> pd.DataFrame:
        """Return a copy of the internal DataFrame."""

        return self._frame.copy()

    def clear(self) -> None:
        """Remove all stored encodings."""

        self._frame = self._frame.iloc[0:0]


_STORE: Optional[RegulatoryStore] = None


def get_store() -> RegulatoryStore:
    """Return the process-wide regulatory store singleton."""

    global _STORE
    if _STORE is None:
        _STORE = RegulatoryStore()
    return _STORE

