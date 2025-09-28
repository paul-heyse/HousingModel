"""Reporting helpers for amenity ROI outputs."""

from __future__ import annotations

from typing import Iterable, List

from .types import AmenityImpactDetail, AmenityImpactSummary


def build_amenity_table(details: Iterable[AmenityImpactDetail]) -> List[dict[str, object]]:
    table: List[dict[str, object]] = []
    for detail in details:
        row = {
            "Amenity": detail.amenity_name,
            "Code": detail.amenity_code,
            "Capex": detail.capex,
            "OpexMonthly": detail.opex_monthly,
            "RentPremiumPerUnit": detail.rent_premium_per_unit,
            "RetentionDeltaBps": detail.retention_delta_bps,
            "MembershipRevenueMonthly": detail.membership_revenue_monthly,
            "AverageMonthlyRent": detail.avg_monthly_rent,
            "UtilizationRate": detail.utilization_rate,
            "PaybackMonths": detail.payback_months,
            "NoiDeltaAnnual": detail.noi_delta_annual,
        }
        table.append(row)
    return table


def build_summary_row(summary: AmenityImpactSummary) -> dict[str, object]:
    return {
        "AssetId": summary.asset_id,
        "TotalCapex": summary.total_capex,
        "TotalOpexMonthly": summary.total_opex_monthly,
        "TotalNoiDeltaAnnual": summary.total_noi_delta_annual,
        "BlendedPaybackMonths": summary.blended_payback_months,
    }


__all__ = ["build_amenity_table", "build_summary_row"]
