"""Default benchmark assumptions for amenity ROI analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from aker_data.amenities import AmenityBenchmark, AmenityBenchmarkStore


@dataclass(frozen=True)
class AmenityCalibration:
    code: str
    name: str
    rent_premium_per_unit: float
    retention_delta_bps: float
    membership_revenue_monthly: float
    avg_monthly_rent: float
    utilization_rate: float
    opex_monthly: float
    capex: float
    data_vintage: str
    source: str


DEFAULT_AMENITY_CALIBRATIONS: Dict[str, AmenityCalibration] = {
    "cowork_lounge": AmenityCalibration(
        code="cowork_lounge",
        name="Cowork Lounge",
        rent_premium_per_unit=85.0,
        retention_delta_bps=180.0,
        membership_revenue_monthly=1200.0,
        avg_monthly_rent=2100.0,
        utilization_rate=0.55,
        opex_monthly=600.0,
        capex=250000.0,
        data_vintage="2025-08",
        source="Aker Benchmarks (Cowork)",
    ),
    "fitness_center": AmenityCalibration(
        code="fitness_center",
        name="Fitness Center Upgrade",
        rent_premium_per_unit=55.0,
        retention_delta_bps=140.0,
        membership_revenue_monthly=450.0,
        avg_monthly_rent=2050.0,
        utilization_rate=0.72,
        opex_monthly=350.0,
        capex=175000.0,
        data_vintage="2025-07",
        source="Aker Benchmarks (Fitness)",
    ),
    "pet_spa": AmenityCalibration(
        code="pet_spa",
        name="Pet Spa & Wash",
        rent_premium_per_unit=35.0,
        retention_delta_bps=120.0,
        membership_revenue_monthly=650.0,
        avg_monthly_rent=1950.0,
        utilization_rate=0.60,
        opex_monthly=280.0,
        capex=95000.0,
        data_vintage="2025-09",
        source="Aker Benchmarks (Pet)",
    ),
    "smart_access": AmenityCalibration(
        code="smart_access",
        name="Smart Access & Package",
        rent_premium_per_unit=25.0,
        retention_delta_bps=90.0,
        membership_revenue_monthly=0.0,
        avg_monthly_rent=1900.0,
        utilization_rate=0.9,
        opex_monthly=150.0,
        capex=60000.0,
        data_vintage="2025-06",
        source="Aker Benchmarks (Smart)",
    ),
}


def seed_default_benchmarks(store: AmenityBenchmarkStore | None = None) -> None:
    target = store or AmenityBenchmarkStore.instance()
    benchmarks = [
        AmenityBenchmark(
            amenity_code=cal.code,
            amenity_name=cal.name,
            rent_premium_per_unit=cal.rent_premium_per_unit,
            retention_delta_bps=cal.retention_delta_bps,
            membership_revenue_monthly=cal.membership_revenue_monthly,
            avg_monthly_rent=cal.avg_monthly_rent,
            utilization_rate=cal.utilization_rate,
            opex_monthly=cal.opex_monthly,
            data_vintage=cal.data_vintage,
            source=cal.source,
            metadata={"default_capex": cal.capex},
        )
        for cal in DEFAULT_AMENITY_CALIBRATIONS.values()
    ]
    target.ingest(benchmarks)


__all__ = ["AmenityCalibration", "DEFAULT_AMENITY_CALIBRATIONS", "seed_default_benchmarks"]
