"""Demographics analysis for urban population and employment data."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from aker_core.logging import get_logger


class DemographicsAnalyzer:
    """Analyzer for demographic and employment data."""

    def __init__(self):
        """Initialize demographics analyzer."""
        self.logger = get_logger(__name__)

    def daytime_population(
        self,
        employment_data: gpd.GeoDataFrame,
        buffer_radius_miles: float = 1.0,
        centroid_points: Optional[List[Point]] = None,
    ) -> Dict[str, int]:
        """Calculate daytime population within buffer zones.

        Args:
            employment_data: GeoDataFrame with employment/workplace data
            buffer_radius_miles: Radius in miles for population calculation
            centroid_points: Optional list of points for buffer centers

        Returns:
            Dictionary with population metrics
        """
        self.logger.info(f"Calculating daytime population within {buffer_radius_miles} mile radius")

        try:
            if centroid_points:
                # Calculate population for each centroid point
                populations = []
                for point in centroid_points:
                    buffer = point.buffer(buffer_radius_miles * 1609.34)  # Convert miles to meters
                    within_buffer = employment_data[employment_data.geometry.within(buffer)]
                    total_employment = (
                        within_buffer["employment"].sum()
                        if "employment" in within_buffer.columns
                        else 0
                    )
                    populations.append(total_employment)

                return {
                    "total_daytime_population": sum(populations),
                    "avg_daytime_population": (
                        sum(populations) / len(populations) if populations else 0
                    ),
                    "max_daytime_population": max(populations) if populations else 0,
                    "min_daytime_population": min(populations) if populations else 0,
                    "buffer_radius_miles": buffer_radius_miles,
                    "analysis_points": len(centroid_points),
                }
            else:
                # Calculate total daytime population
                total_employment = (
                    employment_data["employment"].sum()
                    if "employment" in employment_data.columns
                    else 0
                )

                return {
                    "total_daytime_population": total_employment,
                    "buffer_radius_miles": buffer_radius_miles,
                    "analysis_points": 1,
                }

        except Exception as e:
            self.logger.error(f"Daytime population calculation failed: {e}")
            return {"error": str(e)}

    def employment_density_analysis(
        self, employment_data: gpd.GeoDataFrame, area_bounds: Tuple[float, float, float, float]
    ) -> Dict[str, float]:
        """Analyze employment density and distribution.

        Args:
            employment_data: GeoDataFrame with employment data
            area_bounds: Bounding box (min_lon, min_lat, max_lon, max_lat)

        Returns:
            Dictionary with employment density metrics
        """
        try:
            # Calculate approximate area in square kilometers
            min_lon, min_lat, max_lon, max_lat = area_bounds
            width_km = (max_lon - min_lon) * 111  # Rough conversion
            height_km = (max_lat - min_lat) * 111  # Rough conversion
            area_km2 = width_km * height_km

            total_employment = (
                employment_data["employment"].sum()
                if "employment" in employment_data.columns
                else 0
            )

            return {
                "total_employment": total_employment,
                "area_km2": area_km2,
                "employment_density": total_employment / area_km2 if area_km2 > 0 else 0,
                "employment_points": len(employment_data),
            }

        except Exception as e:
            self.logger.error(f"Employment density analysis failed: {e}")
            return {"error": str(e)}

    def population_flow_analysis(
        self, origin_data: pd.DataFrame, destination_data: pd.DataFrame, flow_column: str = "flow"
    ) -> Dict[str, float]:
        """Analyze population flows between areas.

        Args:
            origin_data: DataFrame with origin population data
            destination_data: DataFrame with destination population data
            flow_column: Column containing flow/migration data

        Returns:
            Dictionary with flow analysis results
        """
        try:
            total_inflow = (
                destination_data[flow_column].sum()
                if flow_column in destination_data.columns
                else 0
            )
            total_outflow = (
                origin_data[flow_column].sum() if flow_column in origin_data.columns else 0
            )

            net_flow = total_inflow - total_outflow

            return {
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "net_flow": net_flow,
                "inflow_rate": (
                    total_inflow / len(destination_data) if len(destination_data) > 0 else 0
                ),
                "outflow_rate": total_outflow / len(origin_data) if len(origin_data) > 0 else 0,
            }

        except Exception as e:
            self.logger.error(f"Population flow analysis failed: {e}")
            return {"error": str(e)}


def daytime_population(
    employment_data: gpd.GeoDataFrame,
    buffer_radius_miles: float = 1.0,
    centroid_points: Optional[List[Point]] = None,
) -> Dict[str, int]:
    """Calculate daytime population within buffer zones.

    Args:
        employment_data: GeoDataFrame with employment/workplace data
        buffer_radius_miles: Radius in miles for population calculation
        centroid_points: Optional list of points for buffer centers

    Returns:
        Dictionary with population metrics
    """
    analyzer = DemographicsAnalyzer()
    return analyzer.daytime_population(employment_data, buffer_radius_miles, centroid_points)
