"""Data models for permit records and related entities."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


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
    property_type: str = Field(..., description="Type of property (residential, commercial, etc.)")
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

    @validator("application_date", "issue_date", "expiration_date", "completion_date")
    def validate_dates(cls, v, field):
        """Validate that dates are reasonable."""
        if v is None:
            return v

        # Check for reasonable date ranges
        if field.name == "application_date":
            # Application date should be in the last 20 years
            if v.year < 2000:
                return v  # Allow older dates for historical data
        elif field.name == "issue_date":
            # Issue date should be after application date
            if hasattr(cls, "application_date"):
                app_date = getattr(cls, "application_date", None)
                if app_date and v < app_date:
                    raise ValueError("Issue date cannot be before application date")
        elif field.name == "completion_date":
            # Completion date should be after issue date
            if hasattr(cls, "issue_date"):
                issue_date = getattr(cls, "issue_date", None)
                if issue_date and v < issue_date:
                    raise ValueError("Completion date cannot be before issue date")

        return v

    @validator("estimated_cost", "actual_cost", "valuation")
    def validate_costs(cls, v):
        """Validate cost values."""
        if v is None:
            return v

        if v < 0:
            raise ValueError("Cost values cannot be negative")

        # Reasonable upper bounds (adjust as needed)
        if v > 100000000:  # $100M
            raise ValueError("Cost values seem unreasonably high")

        return v

    @validator("square_footage")
    def validate_square_footage(cls, v):
        """Validate square footage values."""
        if v is None:
            return v

        if v < 0:
            raise ValueError("Square footage cannot be negative")

        # Reasonable upper bounds
        if v > 1000000:  # 1M sq ft
            raise ValueError("Square footage seems unreasonably high")

        return v

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.dict()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.json()

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
