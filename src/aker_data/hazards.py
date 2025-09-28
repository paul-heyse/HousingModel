"""In-memory hazard dataset registry used by the risk engine and ETL flows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, Mapping, Optional, Tuple


@dataclass(frozen=True)
class HazardRecord:
    """Single hazard severity observation for a subject (market or asset)."""

    subject_type: str
    subject_id: str
    severity_idx: float
    data_vintage: str
    source: str
    metadata: Mapping[str, object] = field(default_factory=dict)


class HazardDataStore:
    """Singleton registry for hazard datasets ingested via ETL pipelines."""

    _instance: "HazardDataStore" | None = None

    def __init__(self) -> None:
        self._store: Dict[str, Dict[Tuple[str, str], HazardRecord]] = {}

    @classmethod
    def instance(cls) -> "HazardDataStore":
        """Return the shared hazard store instance."""

        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def ingest(self, peril: str, records: Iterable[HazardRecord]) -> None:
        """Store or update hazard records for the given peril."""

        if not peril:
            raise ValueError("peril must be a non-empty string")

        bucket = self._store.setdefault(peril.lower(), {})
        for record in records:
            key = (record.subject_type.lower(), record.subject_id)
            bucket[key] = record

    def clear(self) -> None:
        """Remove all stored hazard observations (primarily for testing)."""

        self._store.clear()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get(self, peril: str, subject_type: str, subject_id: str) -> Optional[HazardRecord]:
        """Return the latest hazard record for the subject and peril."""

        bucket = self._store.get(peril.lower())
        if bucket is None:
            return None
        return bucket.get((subject_type.lower(), subject_id))

    def iter_subject_records(self, peril: str) -> Iterator[HazardRecord]:
        """Iterate over all records for a given peril."""

        bucket = self._store.get(peril.lower(), {})
        return iter(bucket.values())

    def list_perils(self) -> Iterable[str]:
        """Return the set of perils available in the store."""

        return list(self._store.keys())


__all__ = ["HazardRecord", "HazardDataStore"]
