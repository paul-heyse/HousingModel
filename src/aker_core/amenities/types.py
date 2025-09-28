"""Typed structures for amenity ROI evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence


@dataclass(frozen=True)
class AmenityInput:
    """Raw amenity scenario supplied to the evaluation engine."""

    amenity_code: str
    capex: Optional[float] = None
    opex_monthly: Optional[float] = None
    rent_premium_per_unit: Optional[float] = None
    retention_delta_bps: Optional[float] = None
    membership_revenue_monthly: Optional[float] = None
    amenity_name: Optional[str] = None
    assumptions: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AmenityImpactDetail:
    """Computed impact for a single amenity."""

    asset_id: int
    amenity_code: str
    amenity_name: str
    capex: float
    opex_monthly: float
    rent_premium_per_unit: float
    retention_delta_bps: float
    membership_revenue_monthly: float
    avg_monthly_rent: float
    utilization_rate: float
    payback_months: Optional[float]
    noi_delta_annual: float
    assumptions: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AmenityImpactSummary:
    """Aggregate results across an amenity package."""

    asset_id: int
    total_capex: float
    total_opex_monthly: float
    total_noi_delta_annual: float
    blended_payback_months: Optional[float]
    entries: Sequence[AmenityImpactDetail]


@dataclass(frozen=True)
class AmenityEvaluationResult:
    """Return payload for `amenity.evaluate`."""

    asset_id: int
    impacts: AmenityImpactSummary
    details: Sequence[AmenityImpactDetail]


__all__ = [
    "AmenityInput",
    "AmenityImpactDetail",
    "AmenityImpactSummary",
    "AmenityEvaluationResult",
]
