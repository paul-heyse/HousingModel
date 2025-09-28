"""Amenity accessibility analysis within isochrones."""

from __future__ import annotations

from typing import Dict, List, Optional

import geopandas as gpd

from aker_core.logging import get_logger


class AmenityAnalyzer:
    """Analyzer for computing amenity accessibility within isochrones."""

    # Standard amenity categories for urban convenience analysis
    AMENITY_CATEGORIES = {
        "grocery": ["supermarket", "grocery", "convenience", "market"],
        "pharmacy": ["pharmacy", "chemist", "drugstore"],
        "healthcare": ["hospital", "clinic", "doctor", "dentist", "urgent_care"],
        "education": ["school", "kindergarten", "university", "college", "library"],
        "transit": ["bus_stop", "subway", "train_station", "light_rail"],
        "recreation": ["park", "playground", "gym", "sports_centre", "swimming_pool"],
        "shopping": ["mall", "shopping", "retail", "department_store"],
        "dining": ["restaurant", "cafe", "fast_food", "bar", "pub"],
        "banking": ["bank", "atm", "credit_union"],
        "services": ["post_office", "government", "police", "fire_station"],
    }

    def __init__(self):
        """Initialize amenity analyzer."""
        self.logger = get_logger(__name__)

    def count_amenities_in_isochrones(
        self,
        isochrones_gdf: gpd.GeoDataFrame,
        amenities_gdf: gpd.GeoDataFrame,
        amenity_categories: Optional[Dict[str, List[str]]] = None,
    ) -> gpd.GeoDataFrame:
        """Count amenities within each isochrone polygon.

        Args:
            isochrones_gdf: GeoDataFrame with isochrone polygons
            amenities_gdf: GeoDataFrame with amenity points
            amenity_categories: Optional custom amenity categories mapping

        Returns:
            GeoDataFrame with amenity counts per isochrone
        """
        categories = amenity_categories or self.AMENITY_CATEGORIES

        self.logger.info(
            f"Counting amenities in {len(isochrones_gdf)} isochrones "
            f"from {len(amenities_gdf)} amenity points"
        )

        # Initialize result columns
        for category in categories.keys():
            isochrones_gdf[f"{category}_count"] = 0

        # Count amenities within each isochrone
        geometry_column = "geometry" if "geometry" in isochrones_gdf.columns else "isochrone"

        for idx, isochrone_row in isochrones_gdf.iterrows():
            isochrone_geom = isochrone_row.get(geometry_column)

            if isochrone_geom is None or isochrone_geom.is_empty:
                continue

            # Find amenities within this isochrone
            within_isochrone = amenities_gdf[amenities_gdf.geometry.within(isochrone_geom)]

            if len(within_isochrone) > 0:
                # Count by category
                for category, keywords in categories.items():
                    category_count = 0

                    for _, amenity in within_isochrone.iterrows():
                        amenity_type = amenity.get("amenity", "").lower()
                        amenity_name = amenity.get("name", "").lower()

                        # Check if amenity matches any keyword in category
                        if any(
                            keyword in amenity_type or keyword in amenity_name
                            for keyword in keywords
                        ):
                            category_count += 1

                    isochrones_gdf.at[idx, f"{category}_count"] = category_count

        # Calculate total amenities
        count_columns = [f"{cat}_count" for cat in categories.keys()]
        isochrones_gdf["total_amenities"] = isochrones_gdf[count_columns].sum(axis=1)

        self.logger.info(f"Completed amenity counting for {len(isochrones_gdf)} isochrones")
        return isochrones_gdf

    def compute_amenity_accessibility_scores(
        self, isochrones_gdf: gpd.GeoDataFrame, weights: Optional[Dict[str, float]] = None
    ) -> gpd.GeoDataFrame:
        """Compute weighted accessibility scores for amenity categories.

        Args:
            isochrones_gdf: GeoDataFrame with amenity counts
            weights: Optional weights for different amenity categories

        Returns:
            GeoDataFrame with accessibility scores
        """
        default_weights = {
            "grocery": 0.25,
            "pharmacy": 0.15,
            "healthcare": 0.20,
            "education": 0.15,
            "transit": 0.10,
            "recreation": 0.10,
            "shopping": 0.05,
        }
        weights = weights or default_weights

        # Calculate weighted score
        score = 0
        for category, weight in weights.items():
            count_col = f"{category}_count"
            if count_col in isochrones_gdf.columns:
                # Normalize by max count in dataset
                max_count = isochrones_gdf[count_col].max()
                if max_count > 0:
                    normalized_count = isochrones_gdf[count_col] / max_count
                    score += normalized_count * weight

        isochrones_gdf["accessibility_score"] = score * 100  # Scale to 0-100

        return isochrones_gdf

    def analyze_amenity_coverage(
        self, isochrones_gdf: gpd.GeoDataFrame, population_gdf: Optional[gpd.GeoDataFrame] = None
    ) -> Dict[str, float]:
        """Analyze amenity coverage and population accessibility.

        Args:
            isochrones_gdf: GeoDataFrame with isochrones and amenity counts
            population_gdf: Optional GeoDataFrame with population data

        Returns:
            Dictionary with coverage analysis results
        """
        analysis = {
            "total_isochrones": len(isochrones_gdf),
            "isochrones_with_amenities": (isochrones_gdf["total_amenities"] > 0).sum(),
            "avg_amenities_per_isochrone": isochrones_gdf["total_amenities"].mean(),
            "max_amenities_per_isochrone": isochrones_gdf["total_amenities"].max(),
        }

        # Analyze by category
        for category in self.AMENITY_CATEGORIES.keys():
            count_col = f"{category}_count"
            if count_col in isochrones_gdf.columns:
                analysis[f"{category}_coverage"] = (isochrones_gdf[count_col] > 0).sum()
                analysis[f"avg_{category}_per_isochrone"] = isochrones_gdf[count_col].mean()

        return analysis

    def create_amenity_heatmap(
        self, isochrones_gdf: gpd.GeoDataFrame, amenity_categories: Optional[List[str]] = None
    ) -> gpd.GeoDataFrame:
        """Create amenity accessibility heatmap data.

        Args:
            isochrones_gdf: GeoDataFrame with isochrones and amenity counts
            amenity_categories: Optional specific categories to include

        Returns:
            GeoDataFrame with heatmap visualization data
        """
        categories = amenity_categories or list(self.AMENITY_CATEGORIES.keys())

        # Create heatmap data
        heatmap_data = []
        for _, row in isochrones_gdf.iterrows():
            for category in categories:
                count_col = f"{category}_count"
                if count_col in row.index:
                    heatmap_data.append(
                        {
                            "geometry": row.geometry.centroid,
                            "category": category,
                            "count": row[count_col],
                            "accessibility_score": row.get("accessibility_score", 0),
                        }
                    )

        if not heatmap_data:
            return gpd.GeoDataFrame()

        return gpd.GeoDataFrame(heatmap_data)


def count_amenities_in_isochrones(
    isochrones_gdf: gpd.GeoDataFrame,
    amenities_gdf: gpd.GeoDataFrame,
    amenity_categories: Optional[Dict[str, List[str]]] = None,
) -> gpd.GeoDataFrame:
    """Count amenities within isochrone polygons.

    Args:
        isochrones_gdf: GeoDataFrame with isochrone polygons
        amenities_gdf: GeoDataFrame with amenity points
        amenity_categories: Optional custom amenity categories mapping

    Returns:
        GeoDataFrame with amenity counts per isochrone
    """
    analyzer = AmenityAnalyzer()
    return analyzer.count_amenities_in_isochrones(isochrones_gdf, amenities_gdf, amenity_categories)
