"""Outdoor recreation and environmental quality analysis for market scoring."""

from .air_quality import AirQualityAnalyzer, pm25_variation
from .models import EnvironmentalDataSource, OutdoorMetrics
from .noise_pollution import NoiseAnalyzer, highway_proximity
from .recreation_access import RecreationAnalyzer, park_accessibility, trail_accessibility
from .smoke_analysis import SmokeAnalyzer, rolling_smoke_days

__all__ = [
    "AirQualityAnalyzer",
    "pm25_variation",
    "NoiseAnalyzer",
    "highway_proximity",
    "RecreationAnalyzer",
    "trail_accessibility",
    "park_accessibility",
    "SmokeAnalyzer",
    "rolling_smoke_days",
    "OutdoorMetrics",
    "EnvironmentalDataSource",
    "compute_outdoor_environmental_metrics",
    "analyze_environmental_risks",
]
