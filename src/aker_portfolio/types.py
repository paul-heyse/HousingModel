from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class PortfolioPosition(BaseModel):
    """Portfolio position representing an individual investment/asset."""

    position_id: Optional[str] = Field(None, description="Unique position identifier")
    asset_id: Optional[str] = Field(None, description="Associated asset identifier")
    msa_id: Optional[str] = Field(None, description="MSA identifier")
    strategy: Optional[str] = Field(None, description="Investment strategy")
    state: Optional[str] = Field(None, description="State code")
    vintage: Optional[int] = Field(None, description="Property vintage year")
    construction_type: Optional[str] = Field(None, description="Construction type")
    rent_band: Optional[str] = Field(None, description="Rent band category")
    position_value: float = Field(..., description="Position value in dollars")
    units: Optional[int] = Field(None, description="Number of units")

    @validator("position_value")
    def validate_position_value(cls, v):
        if v <= 0:
            raise ValueError("Position value must be positive")
        return v


class ExposureDimension(BaseModel):
    """Exposure calculation result for a specific dimension."""

    dimension_type: str = Field(..., description="Type of dimension (strategy, state, etc.)")
    dimension_value: str = Field(..., description="Value of the dimension")
    exposure_pct: float = Field(..., description="Exposure percentage (0-100)")
    exposure_value: float = Field(..., description="Exposure value in dollars")
    total_portfolio_value: float = Field(..., description="Total portfolio value for context")


class ExposureResult(BaseModel):
    """Complete exposure calculation results."""

    as_of_date: datetime = Field(..., description="Date of calculation")
    total_portfolio_value: float = Field(..., description="Total portfolio value")
    exposures: list[ExposureDimension] = Field(..., description="Exposure breakdown by dimensions")
    run_id: Optional[str] = Field(None, description="Associated run identifier")


class ExposureThreshold(BaseModel):
    """Configurable exposure threshold for alerts."""

    threshold_id: Optional[str] = Field(None, description="Threshold identifier")
    dimension_type: str = Field(..., description="Dimension type to monitor")
    dimension_value: Optional[str] = Field(None, description="Specific dimension value (NULL for global)")
    threshold_pct: float = Field(..., description="Threshold percentage")
    threshold_type: str = Field("maximum", description="Threshold type")
    severity_level: str = Field("warning", description="Alert severity level")
    is_active: bool = Field(True, description="Whether threshold is active")


class PortfolioAlert(BaseModel):
    """Alert for threshold breach."""

    alert_id: Optional[str] = Field(None, description="Alert identifier")
    threshold_id: str = Field(..., description="Associated threshold")
    exposure_id: str = Field(..., description="Associated exposure calculation")
    breach_pct: float = Field(..., description="Breach percentage")
    alert_message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Alert severity")
    status: str = Field("active", description="Alert status")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class ExposureRequest(BaseModel):
    """Request for exposure calculation."""

    positions: list[PortfolioPosition] = Field(..., description="Portfolio positions to analyze")
    as_of_date: Optional[datetime] = Field(None, description="Date for calculation (defaults to now)")
    include_alerts: bool = Field(True, description="Whether to check for threshold breaches")


class ExposureComparison(BaseModel):
    """Comparison of current vs previous exposure."""

    current_exposures: ExposureResult = Field(..., description="Current exposure calculation")
    previous_exposures: Optional[ExposureResult] = Field(None, description="Previous exposure calculation")
    changes: list[dict] = Field(..., description="Changes in exposure percentages")
