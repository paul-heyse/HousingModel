"""Urban accessibility analysis for POI counting and convenience scoring."""

from __future__ import annotations

from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd

from aker_core.logging import get_logger
from aker_geo.isochrones import compute_isochrones, count_amenities_in_isochrones
from aker_geo.isochrones.amenity_analysis import AmenityAnalyzer

from .models import AmenityCategory


class AccessibilityAnalyzer:
    """Analyzer for urban accessibility and amenity analysis."""

    def __init__(self):
        """Initialize accessibility analyzer."""
        self.logger = get_logger(__name__)
        self._amenity_analyzer = AmenityAnalyzer()

        # Standard amenity categories for urban convenience
        self.amenity_categories = {
            AmenityCategory.GROCERY: ["supermarket", "grocery", "convenience", "market"],
            AmenityCategory.PHARMACY: ["pharmacy", "chemist", "drugstore"],
            AmenityCategory.HEALTHCARE: ["hospital", "clinic", "doctor", "dentist", "urgent_care"],
            AmenityCategory.EDUCATION: [
                "school",
                "kindergarten",
                "university",
                "college",
                "library",
            ],
            AmenityCategory.TRANSIT: ["bus_stop", "subway", "train_station", "light_rail"],
            AmenityCategory.RECREATION: [
                "park",
                "playground",
                "gym",
                "sports_centre",
                "swimming_pool",
            ],
            AmenityCategory.SHOPPING: ["mall", "shopping", "retail", "department_store"],
            AmenityCategory.DINING: ["restaurant", "cafe", "fast_food", "bar", "pub"],
            AmenityCategory.BANKING: ["bank", "atm", "credit_union"],
            AmenityCategory.SERVICES: ["post_office", "government", "police", "fire_station"],
        }

    def poi_counts(
        self,
        origin_points: List[tuple[float, float]],
        pois_gdf: gpd.GeoDataFrame,
        mode: str = "walk",
        max_time_minutes: int = 15,
        bbox: Optional[tuple[float, float, float, float]] = None,
    ) -> gpd.GeoDataFrame:
        """Count POIs accessible within time limits from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            pois_gdf: GeoDataFrame with POI data
            mode: Transportation mode ("walk", "bike", "drive")
            max_time_minutes: Maximum travel time in minutes
            bbox: Optional bounding box for street network

        Returns:
            GeoDataFrame with POI counts per origin point
        """
        self.logger.info(
            f"Computing POI accessibility for {len(origin_points)} points, "
            f"mode={mode}, max_time={max_time_minutes}min"
        )

        try:
            # Compute isochrones for all origin points
            isochrones_gdf = compute_isochrones(
                origin_points=origin_points, mode=mode, max_time_minutes=max_time_minutes, bbox=bbox
            )

            # Count amenities within each isochrone
            accessibility_gdf = count_amenities_in_isochrones(
                isochrones_gdf, pois_gdf, self.amenity_categories
            )

            # Rename columns to match expected schema
            column_mapping = {
                "grocery_count": "walk_15_grocery_ct" if mode == "walk" else "bike_15_grocery_ct",
                "pharmacy_count": (
                    "walk_15_pharmacy_ct" if mode == "walk" else "bike_15_pharmacy_ct"
                ),
                "healthcare_count": (
                    "walk_15_healthcare_ct" if mode == "walk" else "bike_15_healthcare_ct"
                ),
                "education_count": (
                    "walk_15_education_ct" if mode == "walk" else "bike_15_education_ct"
                ),
                "transit_count": "walk_15_transit_ct" if mode == "walk" else "bike_15_transit_ct",
                "recreation_count": (
                    "walk_15_recreation_ct" if mode == "walk" else "bike_15_recreation_ct"
                ),
                "shopping_count": (
                    "walk_15_shopping_ct" if mode == "walk" else "bike_15_shopping_ct"
                ),
                "dining_count": "walk_15_dining_ct" if mode == "walk" else "bike_15_dining_ct",
                "banking_count": "walk_15_banking_ct" if mode == "walk" else "bike_15_banking_ct",
                "services_count": (
                    "walk_15_services_ct" if mode == "walk" else "bike_15_services_ct"
                ),
                "total_amenities": "walk_15_total_ct" if mode == "walk" else "bike_15_total_ct",
            }

            for old_col, new_col in column_mapping.items():
                if old_col in accessibility_gdf.columns:
                    accessibility_gdf = accessibility_gdf.rename(columns={old_col: new_col})

            self.logger.info(f"Computed accessibility for {len(accessibility_gdf)} origin points")
            return accessibility_gdf

        except Exception as e:
            self.logger.error(f"POI accessibility computation failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Amenity analysis helpers (delegates to aker_geo analyzer)
    # ------------------------------------------------------------------
    def count_amenities_in_isochrones(
        self,
        isochrones_gdf: gpd.GeoDataFrame,
        amenities_gdf: gpd.GeoDataFrame,
        amenity_categories: Optional[Dict[str, List[str]]] = None,
    ) -> gpd.GeoDataFrame:
        """Count amenities present inside each isochrone polygon."""

        from shapely.geometry import Point

        working = isochrones_gdf.copy()
        if "geometry" in working.columns:
            working["geometry"] = working["geometry"].apply(
                lambda geom: geom if geom is not None and not getattr(geom, "is_empty", False) else Point()
            )
        elif "isochrone" in working.columns:
            working["geometry"] = working["isochrone"].apply(
                lambda geom: geom if geom is not None and not getattr(geom, "is_empty", False) else Point()
            )

        result = self._amenity_analyzer.count_amenities_in_isochrones(
            working, amenities_gdf, amenity_categories
        )
        result.index = isochrones_gdf.index
        return result

    def compute_amenity_accessibility_scores(
        self, isochrones_gdf: gpd.GeoDataFrame, weights: Optional[Dict[str, float]] = None
    ) -> gpd.GeoDataFrame:
        """Compute weighted accessibility scores for a set of amenity counts."""

        return self._amenity_analyzer.compute_amenity_accessibility_scores(
            isochrones_gdf.copy(), weights
        )

    def analyze_amenity_coverage(
        self, isochrones_gdf: gpd.GeoDataFrame, population_gdf: Optional[gpd.GeoDataFrame] = None
    ) -> Dict[str, float]:
        """Summarise amenity coverage statistics for the supplied isochrones."""

        return self._amenity_analyzer.analyze_amenity_coverage(isochrones_gdf, population_gdf)

    def rent_trend(
        self, rent_data: pd.DataFrame, periods: int = 4, aggregation_level: str = "msa"
    ) -> Dict[str, float]:
        """Analyze retail rent trends and vacancy patterns.

        Args:
            rent_data: DataFrame with rent and vacancy data
            periods: Number of periods to analyze
            aggregation_level: Level to aggregate ("msa", "city", "zip")

        Returns:
            Dictionary with rent trend metrics
        """
        self.logger.info(f"Analyzing rent trends for {len(rent_data)} records")

        try:
            # Calculate quarter-over-quarter rent changes
            if "asking_rent" in rent_data.columns and "period" in rent_data.columns:
                # Sort by period and calculate changes
                sorted_data = rent_data.sort_values("period")

                # Calculate quarter-over-quarter change
                rent_changes = []
                for i in range(1, len(sorted_data)):
                    prev_rent = sorted_data.iloc[i - 1]["asking_rent"]
                    curr_rent = sorted_data.iloc[i]["asking_rent"]

                    if prev_rent > 0 and curr_rent > 0:
                        change_pct = ((curr_rent - prev_rent) / prev_rent) * 100
                        rent_changes.append(change_pct)

                avg_rent_change = sum(rent_changes) / len(rent_changes) if rent_changes else 0
            else:
                avg_rent_change = 0

            # Calculate vacancy rate
            if "vacant_units" in rent_data.columns and "total_units" in rent_data.columns:
                total_units = rent_data["total_units"].sum()
                vacant_units = rent_data["vacant_units"].sum()

                vacancy_rate = (vacant_units / total_units * 100) if total_units > 0 else 0
            else:
                vacancy_rate = 0

            # Calculate retail health score (inverse of vacancy + rent trend bonus)
            retail_health = 100 - vacancy_rate
            if avg_rent_change > 0:
                retail_health += min(avg_rent_change * 10, 20)  # Positive rent growth bonus

            retail_health = min(retail_health, 100.0)

            result = {
                "retail_vacancy_rate": vacancy_rate,
                "rent_qoq_change": avg_rent_change,
                "retail_health_score": retail_health,
                "data_points": len(rent_data),
                "analysis_periods": periods,
            }

            self.logger.info(
                f"Rent trend analysis complete: vacancy={vacancy_rate:.1f}%, QoQ={avg_rent_change:.1f}%"
            )
            return result

        except Exception as e:
            self.logger.error(f"Rent trend analysis failed: {e}")
            return {
                "retail_vacancy_rate": 0.0,
                "rent_qoq_change": 0.0,
                "retail_health_score": 0.0,
                "error": str(e),
            }


def poi_counts(
    origin_points: List[tuple[float, float]],
    pois_gdf: gpd.GeoDataFrame,
    mode: str = "walk",
    max_time_minutes: int = 15,
    bbox: Optional[tuple[float, float, float, float]] = None,
) -> gpd.GeoDataFrame:
    """Count POIs accessible within time limits from origin points.

    Args:
        origin_points: List of (lat, lon) coordinate tuples
        pois_gdf: GeoDataFrame with POI data
        mode: Transportation mode ("walk", "bike", "drive")
        max_time_minutes: Maximum travel time in minutes
        bbox: Optional bounding box for street network

    Returns:
        GeoDataFrame with POI counts per origin point
    """
    analyzer = AccessibilityAnalyzer()
    return analyzer.poi_counts(origin_points, pois_gdf, mode, max_time_minutes, bbox)


def rent_trend(
    rent_data: pd.DataFrame, periods: int = 4, aggregation_level: str = "msa"
) -> Dict[str, float]:
    """Analyze retail rent trends and vacancy patterns.

    Args:
        rent_data: DataFrame with rent and vacancy data
        periods: Number of periods to analyze
        aggregation_level: Level to aggregate ("msa", "city", "zip")

    Returns:
        Dictionary with rent trend metrics
    """
    analyzer = AccessibilityAnalyzer()
    return analyzer.rent_trend(rent_data, periods, aggregation_level)
