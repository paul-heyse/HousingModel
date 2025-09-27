"""Urban convenience data models and schemas."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class UrbanDataSource(str, Enum):
    """Standardized urban data source types."""

    OSM = "osm"
    GTFS = "gtfs"
    LOCAL_RETAIL = "local_retail"
    LODES = "lodes"
    CENSUS = "census"
    PROPRIETARY = "proprietary"


class AmenityCategory(str, Enum):
    """Standardized amenity categories for urban convenience analysis."""

    GROCERY = "grocery"
    PHARMACY = "pharmacy"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    TRANSIT = "transit"
    RECREATION = "recreation"
    SHOPPING = "shopping"
    DINING = "dining"
    BANKING = "banking"
    SERVICES = "services"


class UrbanMetrics(BaseModel):
    """Standardized urban convenience metrics for market analysis."""

    # Geographic identifiers
    msa_id: str = Field(..., description="MSA identifier")
    msa_name: str = Field(..., description="MSA name")
    state: str = Field(..., description="State abbreviation")

    # 15-minute accessibility counts (walk)
    walk_15_grocery_ct: int = Field(0, description="Grocery stores within 15-min walk")
    walk_15_pharmacy_ct: int = Field(0, description="Pharmacies within 15-min walk")
    walk_15_healthcare_ct: int = Field(0, description="Healthcare facilities within 15-min walk")
    walk_15_education_ct: int = Field(0, description="K-8 schools within 15-min walk")
    walk_15_transit_ct: int = Field(0, description="Transit stops within 15-min walk")
    walk_15_recreation_ct: int = Field(0, description="Recreation facilities within 15-min walk")
    walk_15_shopping_ct: int = Field(0, description="Shopping venues within 15-min walk")
    walk_15_dining_ct: int = Field(0, description="Dining establishments within 15-min walk")
    walk_15_banking_ct: int = Field(0, description="Banking services within 15-min walk")
    walk_15_services_ct: int = Field(0, description="Government/services within 15-min walk")
    walk_15_total_ct: int = Field(0, description="Total amenities within 15-min walk")

    # 15-minute accessibility counts (bike)
    bike_15_grocery_ct: int = Field(0, description="Grocery stores within 15-min bike")
    bike_15_pharmacy_ct: int = Field(0, description="Pharmacies within 15-min bike")
    bike_15_healthcare_ct: int = Field(0, description="Healthcare facilities within 15-min bike")
    bike_15_education_ct: int = Field(0, description="K-8 schools within 15-min bike")
    bike_15_transit_ct: int = Field(0, description="Transit stops within 15-min bike")
    bike_15_recreation_ct: int = Field(0, description="Recreation facilities within 15-min bike")
    bike_15_shopping_ct: int = Field(0, description="Shopping venues within 15-min bike")
    bike_15_dining_ct: int = Field(0, description="Dining establishments within 15-min bike")
    bike_15_banking_ct: int = Field(0, description="Banking services within 15-min bike")
    bike_15_services_ct: int = Field(0, description="Government/services within 15-min bike")
    bike_15_total_ct: int = Field(0, description="Total amenities within 15-min bike")

    # Urban connectivity metrics
    interx_km2: float = Field(0.0, description="Intersection density per square km")
    bikeway_conn_idx: float = Field(0.0, description="Bikeway connectivity index (0-100)")

    # Retail health metrics
    retail_vac: float = Field(0.0, description="Retail vacancy rate percentage")
    retail_rent_qoq: float = Field(0.0, description="Retail rent quarter-over-quarter change")

    # Daytime population metrics
    daytime_pop_1mi: int = Field(0, description="Daytime population within 1-mile radius")

    # Composite scores
    walk_15_score: float = Field(0.0, description="15-minute walk accessibility score (0-100)")
    bike_15_score: float = Field(0.0, description="15-minute bike accessibility score (0-100)")
    connectivity_score: float = Field(0.0, description="Urban connectivity score (0-100)")
    retail_health_score: float = Field(0.0, description="Retail health score (0-100)")
    urban_convenience_score: float = Field(
        0.0, description="Overall urban convenience score (0-100)"
    )

    # Metadata
    data_sources: list[UrbanDataSource] = Field(
        default_factory=list, description="Data sources used"
    )
    last_updated: date = Field(default_factory=date.today, description="Last update date")
    data_quality_score: float = Field(0.0, description="Data quality assessment (0-100)")

    def calculate_composite_scores(self) -> None:
        """Calculate composite scores from individual metrics."""
        # Walk accessibility score (weighted average of amenity counts)
        walk_weights = {
            "grocery": 0.25,
            "pharmacy": 0.15,
            "healthcare": 0.20,
            "education": 0.15,
            "transit": 0.10,
            "recreation": 0.10,
            "shopping": 0.05,
        }

        walk_score = 0
        for category, weight in walk_weights.items():
            count_col = f"walk_15_{category}_ct"
            if hasattr(self, count_col):
                count = getattr(self, count_col)
                # Normalize by max possible (assume 10 of each type is max)
                normalized = min(count / 10.0, 1.0)
                walk_score += normalized * weight

        self.walk_15_score = walk_score * 100

        # Bike accessibility score (similar to walk but with different weights)
        bike_weights = {
            "grocery": 0.20,
            "pharmacy": 0.10,
            "healthcare": 0.15,
            "education": 0.15,
            "transit": 0.15,
            "recreation": 0.15,
            "shopping": 0.10,
        }

        bike_score = 0
        for category, weight in bike_weights.items():
            count_col = f"bike_15_{category}_ct"
            if hasattr(self, count_col):
                count = getattr(self, count_col)
                normalized = min(count / 10.0, 1.0)
                bike_score += normalized * weight

        self.bike_15_score = bike_score * 100

        # Connectivity score (intersection density and bikeway connectivity)
        self.connectivity_score = min(
            (self.interx_km2 / 50.0 * 50)  # Intersection density component (0-50)
            + (self.bikeway_conn_idx / 100.0 * 50),  # Bikeway connectivity component (0-50)
            100.0,
        )

        # Retail health score (inverse of vacancy rate, rent trend)
        retail_health = 100 - self.retail_vac  # Lower vacancy = higher score
        if self.retail_rent_qoq > 0:
            retail_health += min(self.retail_rent_qoq * 10, 20)  # Positive rent growth bonus

        self.retail_health_score = min(retail_health, 100.0)

        # Overall urban convenience score (weighted combination)
        urban_weights = {"walk_15": 0.4, "bike_15": 0.2, "connectivity": 0.2, "retail_health": 0.2}

        self.urban_convenience_score = (
            self.walk_15_score * urban_weights["walk_15"]
            + self.bike_15_score * urban_weights["bike_15"]
            + self.connectivity_score * urban_weights["connectivity"]
            + self.retail_health_score * urban_weights["retail_health"]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict) -> "UrbanMetrics":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "UrbanMetrics":
        """Create from JSON string."""
        import json

        data = json.loads(json_str)
        return cls(**data)
