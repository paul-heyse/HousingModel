"""Amenity ROI evaluation engine."""

from __future__ import annotations

from typing import Iterable, Mapping, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.amenities import AmenityBenchmarkStore
from aker_data.models import Assets

from ..database.amenity import AmenityProgramRepository
from .benchmarks import DEFAULT_AMENITY_CALIBRATIONS, seed_default_benchmarks
from .types import (
    AmenityEvaluationResult,
    AmenityImpactDetail,
    AmenityImpactSummary,
    AmenityInput,
)

DEFAULT_UNITS = 120
DEFAULT_CALCULATION_METHOD = "amenity_roi_linear_v1"


class AmenityEngine:
    """Evaluate amenity ROI using benchmarks and asset context."""

    def __init__(
        self,
        session: Session,
        *,
        benchmark_store: Optional[AmenityBenchmarkStore] = None,
    ) -> None:
        self.session = session
        self.benchmark_store = benchmark_store or AmenityBenchmarkStore.instance()
        if not self.benchmark_store.list_codes():
            seed_default_benchmarks(self.benchmark_store)
        self.repository = AmenityProgramRepository(session)

    # ------------------------------------------------------------------
    def evaluate(
        self,
        asset_id: int,
        amenities: Sequence[AmenityInput],
        *,
        run_id: Optional[int] = None,
        data_vintage: Optional[str] = None,
    ) -> AmenityEvaluationResult:
        units = self._get_units(asset_id)
        details: list[AmenityImpactDetail] = []

        for amenity in amenities:
            detail = self._evaluate_single(asset_id, amenity, units)
            self.repository.upsert(
                detail,
                run_id=run_id,
                calculation_method=DEFAULT_CALCULATION_METHOD,
                data_vintage=data_vintage,
                assumptions=dict(detail.assumptions),
            )
            details.append(detail)

        summary = self._summarise(asset_id, details)
        return AmenityEvaluationResult(asset_id=asset_id, impacts=summary, details=tuple(details))

    # ------------------------------------------------------------------
    def _get_units(self, asset_id: int) -> int:
        stmt = select(Assets.units).where(Assets.asset_id == asset_id)
        units = self.session.execute(stmt).scalar_one_or_none()
        if units is None or units <= 0:
            return DEFAULT_UNITS
        return int(units)

    def _evaluate_single(
        self,
        asset_id: int,
        amenity: AmenityInput,
        units: int,
    ) -> AmenityImpactDetail:
        benchmark = self.benchmark_store.get(amenity.amenity_code)
        if benchmark is None:
            calibration = DEFAULT_AMENITY_CALIBRATIONS.get(amenity.amenity_code)
            if calibration:
                seed_default_benchmarks(self.benchmark_store)
                benchmark = self.benchmark_store.get(amenity.amenity_code)

        capex = amenity.capex
        opex_monthly = amenity.opex_monthly
        rent_premium_per_unit = amenity.rent_premium_per_unit
        retention_delta_bps = amenity.retention_delta_bps
        membership_revenue_monthly = amenity.membership_revenue_monthly
        amenity_name = amenity.amenity_name or amenity.amenity_code.replace("_", " ").title()
        avg_monthly_rent = None
        utilization_rate = None
        source = "manual"
        metadata: Mapping[str, object] = amenity.assumptions

        if benchmark is not None:
            amenity_name = amenity_name or benchmark.amenity_name
            if rent_premium_per_unit is None:
                rent_premium_per_unit = benchmark.rent_premium_per_unit
            if retention_delta_bps is None:
                retention_delta_bps = benchmark.retention_delta_bps
            if membership_revenue_monthly is None:
                membership_revenue_monthly = benchmark.membership_revenue_monthly
            avg_monthly_rent = benchmark.avg_monthly_rent
            utilization_rate = benchmark.utilization_rate
            if opex_monthly is None:
                opex_monthly = benchmark.opex_monthly
            if capex is None and "default_capex" in benchmark.metadata:
                capex = float(benchmark.metadata["default_capex"])  # type: ignore[arg-type]
            source = benchmark.source
            metadata = {**benchmark.metadata, **metadata}

        capex = capex or 0.0
        opex_monthly = opex_monthly or 0.0
        rent_premium_per_unit = rent_premium_per_unit or 0.0
        retention_delta_bps = retention_delta_bps or 0.0
        membership_revenue_monthly = membership_revenue_monthly or 0.0
        avg_monthly_rent = avg_monthly_rent or 2000.0
        utilization_rate = utilization_rate if utilization_rate is not None else 0.6

        monthly_premium = rent_premium_per_unit * units
        retention_value = (retention_delta_bps / 10_000.0) * avg_monthly_rent * units
        membership_value = membership_revenue_monthly * utilization_rate
        total_monthly_benefit = monthly_premium + retention_value + membership_value
        monthly_noi_delta = total_monthly_benefit - opex_monthly
        noi_delta_annual = monthly_noi_delta * 12.0
        payback_months = capex / monthly_noi_delta if monthly_noi_delta > 1e-6 else None

        assumptions = {
            "units": units,
            "monthly_premium": monthly_premium,
            "retention_value": retention_value,
            "membership_value": membership_value,
            "source": source,
            **metadata,
        }

        return AmenityImpactDetail(
            asset_id=asset_id,
            amenity_code=amenity.amenity_code,
            amenity_name=amenity_name,
            capex=capex,
            opex_monthly=opex_monthly,
            rent_premium_per_unit=rent_premium_per_unit,
            retention_delta_bps=retention_delta_bps,
            membership_revenue_monthly=membership_revenue_monthly,
            avg_monthly_rent=avg_monthly_rent,
            utilization_rate=utilization_rate,
            payback_months=payback_months,
            noi_delta_annual=noi_delta_annual,
            assumptions=assumptions,
        )

    def _summarise(self, asset_id: int, details: Iterable[AmenityImpactDetail]) -> AmenityImpactSummary:
        detail_list = list(details)
        total_capex = sum(detail.capex for detail in detail_list)
        total_opex = sum(detail.opex_monthly for detail in detail_list)
        total_noi_annual = sum(detail.noi_delta_annual for detail in detail_list)
        monthly_noi = total_noi_annual / 12.0
        blended_payback = total_capex / monthly_noi if monthly_noi > 1e-6 else None

        return AmenityImpactSummary(
            asset_id=asset_id,
            total_capex=total_capex,
            total_opex_monthly=total_opex,
            total_noi_delta_annual=total_noi_annual,
            blended_payback_months=blended_payback,
            entries=tuple(detail_list),
        )


def evaluate(
    *,
    session: Session,
    asset_id: int,
    amenities: Sequence[AmenityInput],
    run_id: Optional[int] = None,
    data_vintage: Optional[str] = None,
) -> AmenityEvaluationResult:
    """Convenience wrapper mirroring the spec signature."""

    engine = AmenityEngine(session)
    return engine.evaluate(asset_id, amenities, run_id=run_id, data_vintage=data_vintage)


__all__ = ["AmenityEngine", "evaluate"]
