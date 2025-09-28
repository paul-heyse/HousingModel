"""Persistence helpers for amenity program evaluations."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from aker_data.models import AmenityProgram

from ..amenities.types import AmenityImpactDetail


class AmenityProgramRepository:
    """Read/write access to amenity program evaluation results."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        detail: AmenityImpactDetail,
        *,
        run_id: Optional[int] = None,
        calculation_method: Optional[str] = None,
        data_vintage: Optional[str] = None,
        assumptions: Optional[dict[str, object]] = None,
    ) -> AmenityProgram:
        stmt = select(AmenityProgram).where(
            AmenityProgram.asset_id == detail.asset_id,
            AmenityProgram.amenity_code == detail.amenity_code,
        )
        record = self.session.execute(stmt).scalar_one_or_none()

        payload = {
            "amenity_name": detail.amenity_name,
            "capex": detail.capex,
            "opex_monthly": detail.opex_monthly,
            "rent_premium_per_unit": detail.rent_premium_per_unit,
            "retention_delta_bps": detail.retention_delta_bps,
            "membership_revenue_monthly": detail.membership_revenue_monthly,
            "avg_monthly_rent": detail.avg_monthly_rent,
            "utilization_rate": detail.utilization_rate,
            "payback_months": detail.payback_months,
            "noi_delta_annual": detail.noi_delta_annual,
            "assumptions": assumptions or detail.assumptions,
        }
        if run_id is not None:
            payload["run_id"] = run_id
        if calculation_method is not None:
            payload["calculation_method"] = calculation_method
        if data_vintage is not None:
            payload["data_vintage"] = data_vintage

        if record is None:
            record = AmenityProgram(
                asset_id=detail.asset_id,
                amenity_code=detail.amenity_code,
                **payload,
            )
            self.session.add(record)
        else:
            for key, value in payload.items():
                setattr(record, key, value)

        self.session.flush()
        return record

    def list_for_asset(self, asset_id: int) -> list[AmenityProgram]:
        stmt = select(AmenityProgram).where(AmenityProgram.asset_id == asset_id)
        return list(self.session.execute(stmt).scalars())


__all__ = ["AmenityProgramRepository"]
