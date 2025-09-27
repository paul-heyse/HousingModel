"""Wildfire smoke analysis for air quality impact assessment."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

from aker_core.logging import get_logger

from ..connectors.base import DataConnector
from .models import SmokeDensity


class NOAAHMSConnector(DataConnector):
    """Connector for NOAA HMS (Hazard Mapping System) smoke data."""

    def __init__(self, **kwargs):
        """Initialize NOAA HMS connector."""
        super().__init__(
            name="noaa_hms",
            base_url="https://satepsanone.nesdis.noaa.gov",
            output_schema={
                "smoke_id": "string",
                "date": "datetime64[ns]",
                "density": "string",
                "latitude": "float64",
                "longitude": "float64",
                "geometry": "object",  # GeoJSON-like geometry
                "source": "string",
                "collected_at": "datetime64[ns]",
            },
            **kwargs
        )

    def _fetch_raw_data(
        self,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """Fetch smoke data from NOAA HMS."""
        # NOAA HMS provides smoke plume data
        # This is a simplified implementation - real implementation would use their API
        # For now, return mock data for testing

        # Generate mock smoke data for the date range
        mock_data = []
        current_date = start_date

        while current_date <= end_date:
            # Generate 1-5 smoke events per day (simplified)
            num_events = self._get_random_int(1, 5)

            for i in range(num_events):
                # Generate random smoke event in US bounds
                lat = self._get_random_float(25.0, 49.0)  # Continental US latitudes
                lon = self._get_random_float(-125.0, -67.0)  # Continental US longitudes

                # Random density
                density = self._get_random_choice(["Light", "Moderate", "Heavy"])

                mock_data.append({
                    "smoke_id": f"HMS_{current_date.strftime('%Y%m%d')}_{i"03d"}",
                    "date": current_date,
                    "density": density,
                    "latitude": lat,
                    "longitude": lon,
                    "source": "noaa_hms"
                })

            current_date += timedelta(days=1)

        return pd.DataFrame(mock_data)

    def _get_random_float(self, min_val: float, max_val: float) -> float:
        """Get random float between min and max."""
        import random
        return random.uniform(min_val, max_val)

    def _get_random_int(self, min_val: int, max_val: int) -> int:
        """Get random int between min and max."""
        import random
        return random.randint(min_val, max_val)

    def _get_random_choice(self, choices: List[str]) -> str:
        """Get random choice from list."""
        import random
        return random.choice(choices)

    def _transform_to_dataframe(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Transform NOAA HMS data to standardized format."""
        df = super()._transform_to_dataframe(raw_data)

        # Add geometry column from lat/lon
        df['geometry'] = df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)

        # Add metadata
        df["source_system"] = "noaa_hms_api"
        df["collected_at"] = pd.Timestamp.now()

        return df


class SmokeAnalyzer:
    """Analyzer for wildfire smoke impact and exposure analysis."""

    def __init__(self):
        """Initialize smoke analyzer."""
        self.logger = get_logger(__name__)

        # Smoke density thresholds (simplified)
        self.density_thresholds = {
            "light": 1,
            "moderate": 2,
            "heavy": 3,
            "extreme": 4
        }

    def rolling_smoke_days(
        self,
        smoke_data: gpd.GeoDataFrame,
        msa_bounds: Tuple[float, float, float, float],
        window_days: int = 30,
        aggregation_level: str = "daily"
    ) -> Dict[str, int]:
        """Calculate rolling smoke exposure days within MSA bounds.

        Args:
            smoke_data: GeoDataFrame with smoke plume data
            msa_bounds: MSA bounding box (min_lon, min_lat, max_lon, max_lat)
            window_days: Rolling window size in days
            aggregation_level: Aggregation level ("daily", "weekly", "monthly")

        Returns:
            Dictionary with smoke exposure metrics
        """
        self.logger.info(f"Analyzing smoke exposure for {window_days}-day window")

        try:
            # Filter smoke data to MSA bounds
            min_lon, min_lat, max_lon, max_lat = msa_bounds

            # Create bounding box polygon
            bbox_poly = Polygon([
                (min_lon, min_lat),
                (max_lon, min_lat),
                (max_lon, max_lat),
                (min_lon, max_lat),
                (min_lon, min_lat)
            ])

            # Filter smoke events within MSA bounds
            within_msa = smoke_data[smoke_data.geometry.within(bbox_poly)]

            if len(within_msa) == 0:
                return {"smoke_days": 0, "max_density": "none", "avg_density_score": 0}

            # Calculate smoke days by date
            smoke_by_date = within_msa.groupby('date').agg({
                'density': lambda x: max([self.density_thresholds.get(d, 0) for d in x]),
                'smoke_id': 'count'
            }).rename(columns={'smoke_id': 'events'})

            # Calculate rolling statistics
            if aggregation_level == "daily":
                # Daily smoke days
                smoke_days = len(smoke_by_date)
            elif aggregation_level == "weekly":
                # Weekly rolling average
                smoke_days = len(smoke_by_date)  # Simplified - would need proper rolling calculation
            elif aggregation_level == "monthly":
                # Monthly rolling average
                smoke_days = len(smoke_by_date)  # Simplified
            else:
                smoke_days = len(smoke_by_date)

            # Calculate max density
            max_density_score = smoke_by_date['density'].max() if len(smoke_by_date) > 0 else 0
            max_density = self._score_to_density(max_density_score)

            # Calculate average density score
            avg_density_score = smoke_by_date['density'].mean() if len(smoke_by_date) > 0 else 0

            result = {
                "smoke_days": smoke_days,
                "max_density": max_density,
                "avg_density_score": avg_density_score,
                "total_events": len(within_msa),
                "window_days": window_days,
                "aggregation_level": aggregation_level
            }

            self.logger.info(f"Smoke analysis complete: {smoke_days} days, max density: {max_density}")
            return result

        except Exception as e:
            self.logger.error(f"Smoke analysis failed: {e}")
            return {"error": str(e)}

    def _score_to_density(self, score: int) -> str:
        """Convert numeric density score to categorical density."""
        if score >= 4:
            return "extreme"
        elif score >= 3:
            return "heavy"
        elif score >= 2:
            return "moderate"
        elif score >= 1:
            return "light"
        else:
            return "none"

    def smoke_impact_score(
        self,
        smoke_days: int,
        max_density: str,
        population: Optional[int] = None
    ) -> float:
        """Calculate smoke impact score (0-100).

        Args:
            smoke_days: Number of smoke days
            max_density: Maximum smoke density level
            population: Optional population for impact weighting

        Returns:
            Smoke impact score (0-100)
        """
        # Base score from smoke days (0-50 points)
        days_score = min(smoke_days / 30.0 * 50, 50)  # Max 50 points for 30+ days

        # Density multiplier (0-50 points)
        density_multipliers = {
            "none": 0,
            "light": 0.2,
            "moderate": 0.5,
            "heavy": 0.8,
            "extreme": 1.0
        }
        density_score = density_multipliers.get(max_density, 0) * 50

        # Population weighting (if provided)
        if population:
            # Higher population = higher impact score
            pop_factor = min(population / 1000000, 1.0)  # Normalize to millions
            total_score = (days_score + density_score) * (1 + pop_factor * 0.2)
        else:
            total_score = days_score + density_score

        return min(total_score, 100.0)


def rolling_smoke_days(
    smoke_data: gpd.GeoDataFrame,
    msa_bounds: Tuple[float, float, float, float],
    window_days: int = 30,
    aggregation_level: str = "daily"
) -> Dict[str, int]:
    """Calculate rolling smoke exposure days within MSA bounds.

    Args:
        smoke_data: GeoDataFrame with smoke plume data
        msa_bounds: MSA bounding box (min_lon, min_lat, max_lon, max_lat)
        window_days: Rolling window size in days
        aggregation_level: Aggregation level

    Returns:
        Dictionary with smoke exposure metrics
    """
    analyzer = SmokeAnalyzer()
    return analyzer.rolling_smoke_days(smoke_data, msa_bounds, window_days, aggregation_level)
