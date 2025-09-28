"""In-memory benchmark registry for amenity ROI evaluations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, Optional


@dataclass(frozen=True)
class AmenityBenchmark:
    """Benchmark assumptions for an amenity code."""

    amenity_code: str
    amenity_name: str
    rent_premium_per_unit: float
    retention_delta_bps: float
    membership_revenue_monthly: float
    avg_monthly_rent: float
    utilization_rate: float
    opex_monthly: float
    data_vintage: str
    source: str
    metadata: Mapping[str, object] = field(default_factory=dict)


class AmenityBenchmarkStore:
    """Simple registry filled by ETL pipelines for amenity benchmarks."""

    _instance: "AmenityBenchmarkStore" | None = None

    def __init__(self) -> None:
        self._benchmarks: Dict[str, AmenityBenchmark] = {}

    @classmethod
    def instance(cls) -> "AmenityBenchmarkStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ingest(self, benchmarks: Iterable[AmenityBenchmark]) -> None:
        for item in benchmarks:
            self._benchmarks[item.amenity_code.lower()] = item

    def get(self, amenity_code: str) -> Optional[AmenityBenchmark]:
        return self._benchmarks.get(amenity_code.lower())

    def clear(self) -> None:
        self._benchmarks.clear()

    def list_codes(self) -> Iterable[str]:
        return list(self._benchmarks.keys())


__all__ = ["AmenityBenchmark", "AmenityBenchmarkStore"]
