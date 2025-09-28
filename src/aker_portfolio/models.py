from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from aker_data.base import Base


class PortfolioPositions(Base):
    """Portfolio position records representing individual investments/assets."""

    __tablename__ = "portfolio_positions"

    position_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    asset_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    msa_id: Mapped[Optional[str]] = mapped_column(String(12), index=True)
    strategy: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), index=True)
    vintage: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    construction_type: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    rent_band: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    position_value: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class PortfolioExposures(Base):
    """Aggregated portfolio exposure calculations by dimension."""

    __tablename__ = "portfolio_exposures"

    exposure_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dimension_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # strategy, state, msa, vintage, etc.
    dimension_value: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    exposure_pct: Mapped[float] = mapped_column(Float, nullable=False)
    exposure_value: Mapped[float] = mapped_column(Float, nullable=False)
    total_portfolio_value: Mapped[float] = mapped_column(Float, nullable=False)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "dimension_type", "dimension_value", "as_of_date", name="uq_exposure_dimension_date"
        ),
    )


class ExposureThresholds(Base):
    """Configurable exposure thresholds for alert generation."""

    __tablename__ = "exposure_thresholds"

    threshold_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dimension_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    dimension_value: Mapped[Optional[str]] = mapped_column(String(100), index=True)  # NULL for global
    threshold_pct: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="maximum"
    )  # maximum, minimum
    severity_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="warning"
    )  # warning, critical
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class PortfolioAlerts(Base):
    """Alert records for threshold breaches."""

    __tablename__ = "portfolio_alerts"

    alert_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    threshold_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("exposure_thresholds.threshold_id"), nullable=False
    )
    exposure_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("portfolio_exposures.exposure_id"), nullable=False
    )
    breach_pct: Mapped[float] = mapped_column(Float, nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, acknowledged, resolved
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(100))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'acknowledged', 'resolved')",
            name="check_alert_status"
        ),
    )
