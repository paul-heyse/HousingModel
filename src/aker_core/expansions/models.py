"""Data models for economic expansion events."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpansionEvent(BaseModel):
    """Structured representation of an economic development announcement."""

    company: str = Field(..., description="Company or organisation announcing the expansion")
    summary: str = Field(..., description="Short summary of the expansion announcement")
    publication_date: datetime = Field(
        ..., description="Publication timestamp supplied by the source feed"
    )
    source: str = Field(..., description="Feed or source identifier")
    source_url: str = Field(..., description="Canonical URL for the announcement")

    # Optional enriched fields produced by the ingestor
    city: Optional[str] = Field(None, description="Detected city for the expansion")
    state: Optional[str] = Field(None, description="Detected US state or region")
    country: Optional[str] = Field(None, description="Country for the expansion location")
    facility_location: Optional[str] = Field(
        None, description="Free-form text representing the facility location"
    )
    latitude: Optional[float] = Field(None, description="Latitude derived from geocoding")
    longitude: Optional[float] = Field(None, description="Longitude derived from geocoding")
    geocode_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Geocoding confidence score")
    geocode_provider: Optional[str] = Field(None, description="Provider used for geocoding")
    jobs_created: Optional[int] = Field(
        None, description="Number of jobs the expansion is expected to create"
    )
    investment_amount: Optional[float] = Field(
        None, description="Investment amount expressed in millions of dollars"
    )
    currency: Optional[str] = Field(None, description="Currency for the investment amount")
    event_type: Optional[str] = Field(
        None, description="Categorised event style (new facility, etc.)"
    )
    industry: Optional[str] = Field(None, description="Industry or sector for the announcement")
    timeline: Optional[str] = Field(None, description="Expansion timeline information")
    tags: List[str] = Field(default_factory=list, description="Tags applied during enrichment")
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the extracted information",
    )
    company_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence score for company extraction"
    )
    location_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence score for location extraction"
    )
    industry_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence score for industry classification"
    )
    jobs_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence score for jobs extraction"
    )
    investment_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence score for investment extraction"
    )
    review_required: bool = Field(
        False, description="Flag indicating that manual review has been requested"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata payload")
    raw_text: str = Field(
        ...,
        description="Raw article or press release text used for extraction for provenance and audits",
    )
    anomaly_score: Dict[str, Optional[float]] = Field(
        default_factory=dict, description="Anomaly scoring metadata"
    )
    anomaly_flags: List[str] = Field(default_factory=list, description="Anomaly reason codes")

    @field_validator("company")
    def _normalise_company(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("company must not be blank")
        return clean

    @field_validator("jobs_created")
    def _validate_jobs(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("jobs_created cannot be negative")
        return value

    @field_validator("investment_amount")
    def _validate_investment(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("investment_amount cannot be negative")
        return value

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        json_encoders={datetime: lambda dt: dt.isoformat()},
    )
