"""Outdoor recreation and environmental quality data models."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class EnvironmentalDataSource(str, Enum):
    """Standardized environmental data source types."""

    EPA_AIRNOW = "epa_airnow"
    NOAA_HMS = "noaa_hms"
    USGS_DEM = "usgs_dem"
    OSM_TRAILS = "osm_trails"
    OSM_PARKS = "osm_parks"
    GTFS_TRANSIT = "gtfs_transit"
    NHD_WATERWAYS = "nhd_waterways"
    FEMA_NFHL = "fema_nfhl"
    LOCAL_PERMITS = "local_permits"
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


class AirQualityLevel(str, Enum):
    """Air quality levels based on PM2.5 concentrations."""

    GOOD = "good"  # 0-12 μg/m³
    MODERATE = "moderate"  # 12.1-35.4 μg/m³
    UNHEALTHY_SENSITIVE = "unhealthy_sensitive"  # 35.5-55.4 μg/m³
    UNHEALTHY = "unhealthy"  # 55.5-150.4 μg/m³
    VERY_UNHEALTHY = "very_unhealthy"  # 150.5-250.4 μg/m³
    HAZARDOUS = "hazardous"  # 250.5+ μg/m³


class SmokeDensity(str, Enum):
    """Smoke density classifications."""

    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"


class NoiseLevel(str, Enum):
    """Noise level classifications."""

    QUIET = "quiet"  # < 50 dB
    MODERATE = "moderate"  # 50-65 dB
    LOUD = "loud"  # 65-80 dB
    VERY_LOUD = "very_loud"  # 80-95 dB
    EXTREME = "extreme"  # > 95 dB


class OutdoorMetrics(BaseModel):
    """Standardized outdoor recreation and environmental quality metrics."""

    # Geographic identifiers
    msa_id: str = Field(..., description="MSA identifier")
    msa_name: str = Field(..., description="MSA name")
    state: str = Field(..., description="State abbreviation")

    # Minutes to outdoor amenities
    min_trail_min: float = Field(0.0, description="Minutes to nearest trailhead")
    min_ski_bus_min: float = Field(0.0, description="Minutes to nearest ski bus")
    min_water_min: float = Field(0.0, description="Minutes to nearest water body")
    park_min: float = Field(0.0, description="Minutes to nearest regional park")

    # Trail and outdoor access metrics
    trail_mi_pc: float = Field(0.0, description="Trail miles per capita")
    public_land_30min_pct: float = Field(0.0, description="Public land % within 30-min drive")

    # Air quality metrics
    pm25_var: float = Field(0.0, description="PM2.5 seasonal variation index")
    smoke_days: int = Field(0, description="Annual wildfire smoke days")
    air_quality_score: float = Field(0.0, description="Air quality score (0-100)")

    # Noise pollution metrics
    hw_rail_prox_idx: float = Field(0.0, description="Highway/rail proximity index")
    noise_level: NoiseLevel = Field(NoiseLevel.QUIET, description="Noise level classification")
    noise_score: float = Field(0.0, description="Noise pollution score (0-100)")

    # Composite outdoor scores
    outdoor_recreation_score: float = Field(
        0.0, description="Outdoor recreation accessibility (0-100)"
    )
    environmental_quality_score: float = Field(
        0.0, description="Environmental quality score (0-100)"
    )
    outdoor_lifestyle_score: float = Field(
        0.0, description="Overall outdoor lifestyle score (0-100)"
    )

    # Metadata
    data_sources: list[EnvironmentalDataSource] = Field(
        default_factory=list, description="Data sources used"
    )
    last_updated: date = Field(default_factory=date.today, description="Last update date")
    data_quality_score: float = Field(0.0, description="Data quality assessment (0-100)")

    def calculate_composite_scores(self) -> None:
        """Calculate composite outdoor scores from individual metrics."""
        # Outdoor recreation score (weighted average of access metrics)
        recreation_weights = {
            "trail_access": 0.25,
            "ski_access": 0.20,
            "water_access": 0.20,
            "park_access": 0.20,
            "trail_density": 0.15,
        }

        recreation_score = 0
        for metric, weight in recreation_weights.items():
            if metric == "trail_access":
                score = max(0, 100 - self.min_trail_min * 2)  # Closer = higher score
            elif metric == "ski_access":
                score = max(0, 100 - self.min_ski_bus_min * 1.5)
            elif metric == "water_access":
                score = max(0, 100 - self.min_water_min * 1.5)
            elif metric == "park_access":
                score = max(0, 100 - self.park_min * 1.5)
            elif metric == "trail_density":
                score = min(self.trail_mi_pc * 20, 100)  # Normalize to 0-100

            recreation_score += score * weight

        self.outdoor_recreation_score = recreation_score

        # Environmental quality score (air quality and noise)
        env_weights = {"air_quality": 0.6, "noise_pollution": 0.4}

        self.environmental_quality_score = (
            self.air_quality_score * env_weights["air_quality"]
            + (100 - self.hw_rail_prox_idx * 20)
            * env_weights["noise_pollution"]  # Lower proximity = higher score
        )

        # Overall outdoor lifestyle score (weighted combination)
        lifestyle_weights = {"recreation": 0.5, "environment": 0.3, "density": 0.2}

        self.outdoor_lifestyle_score = (
            self.outdoor_recreation_score * lifestyle_weights["recreation"]
            + self.environmental_quality_score * lifestyle_weights["environment"]
            + min(self.public_land_30min_pct * 2, 100) * lifestyle_weights["density"]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict) -> "OutdoorMetrics":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "OutdoorMetrics":
        """Create from JSON string."""
        import json

        data = json.loads(json_str)
        return cls(**data)
