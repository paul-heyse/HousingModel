"""Data models for permit records and related entities."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PermitStatus(str, Enum):
    """Standardized permit status values."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    UNDER_REVIEW = "under_review"
    ISSUED = "issued"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PermitType(str, Enum):
    """Standardized permit type classifications."""

    RESIDENTIAL_NEW = "residential_new"
    RESIDENTIAL_RENOVATION = "residential_renovation"
    COMMERCIAL_NEW = "commercial_new"
    COMMERCIAL_RENOVATION = "commercial_renovation"
    DEMOLITION = "demolition"
    ADDITION = "addition"
    POOL = "pool"
    GARAGE = "garage"
    DECK = "deck"
    FENCE = "fence"
    OTHER = "other"


class Address(BaseModel):
    """Standardized address information."""

    street: str
    city: str
    state: str
    zip_code: str
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PermitRecord(BaseModel):
    """Standardized permit record model."""

    # Core permit information
    permit_id: str = Field(..., description="Unique permit identifier")
    permit_type: PermitType = Field(..., description="Type of permit")
    status: PermitStatus = Field(..., description="Current permit status")
    description: str = Field(..., description="Description of the permitted work")

    # Dates
    application_date: date = Field(..., description="Date permit was applied for")
    issue_date: Optional[date] = Field(None, description="Date permit was issued")
    expiration_date: Optional[date] = Field(None, description="Date permit expires")
    completion_date: Optional[date] = Field(None, description="Date work was completed")

    # Financial information
    estimated_cost: Optional[float] = Field(None, description="Estimated cost of work")
    actual_cost: Optional[float] = Field(None, description="Actual cost of work")
    valuation: Optional[float] = Field(None, description="Property valuation")

    # Property information
    address: Address = Field(..., description="Property address")
    property_type: Optional[str] = Field(
        None, description="Type of property (residential, commercial, etc.)"
    )
    square_footage: Optional[int] = Field(None, description="Square footage of work area")

    # Applicant information
    applicant_name: str = Field(..., description="Name of permit applicant")
    applicant_address: Optional[str] = Field(None, description="Address of applicant")
    contractor_name: Optional[str] = Field(None, description="Contractor name if applicable")
    contractor_license: Optional[str] = Field(None, description="Contractor license number")

    # Metadata
    source_system: str = Field(..., description="Source system identifier")
    source_url: Optional[str] = Field(None, description="Original source URL")
    collected_at: datetime = Field(
        default_factory=datetime.now, description="When data was collected"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="When record was last updated"
    )

    # Validation flags
    data_quality_issues: list[str] = Field(
        default_factory=list, description="Data quality issues found"
    )
    processing_errors: list[str] = Field(
        default_factory=list, description="Processing errors encountered"
    )

    @field_validator("estimated_cost", "actual_cost", "valuation")
    @classmethod
    def _ensure_non_negative(cls, value: Optional[float]) -> Optional[float]:
        """Ensure monetary fields are non-negative."""
        if value is not None and value < 0:
            raise ValueError("Cost values cannot be negative")
        return value

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict) -> "PermitRecord":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "PermitRecord":
        """Create from JSON string."""
        import json

        data = json.loads(json_str)
        return cls(**data)


class PermitCollectionResult:
    """Result of permit collection operation."""

    def __init__(
        self,
        permits: list[PermitRecord],
        collection_metadata: dict[str, any],
        errors: list[str] = None,
    ):
        self.permits = permits
        self.collection_metadata = collection_metadata
        self.errors = errors or []

    @property
    def success(self) -> bool:
        """Whether collection was successful."""
        return len(self.errors) == 0

    @property
    def total_permits(self) -> int:
        """Total number of permits collected."""
        return len(self.permits)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "total_permits": self.total_permits,
            "collection_metadata": self.collection_metadata,
            "errors": self.errors,
            "success": self.success,
        }
