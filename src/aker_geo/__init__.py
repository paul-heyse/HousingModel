"""Geospatial utilities for coordinate reference system transformations and spatial data validation."""

import geopandas as gpd

from .crs import to_storage, to_ui
from .isochrones import compute_isochrones, count_amenities_in_isochrones
from .terrain import (
    DigitalElevationModel,
    analyze_noise,
    analyze_viewshed,
    assess_parcel_buffers,
    combine_overlay_results,
    compute_constraint_scores,
    load_nhd_waterways,
    load_usgs_dem,
    slope_percent,
    waterway,
)
from .validate import validate_crs, validate_geometry

__all__ = [
    "to_storage",
    "to_ui",
    "compute_isochrones",
    "count_amenities_in_isochrones",
    "validate_geometry",
    "validate_crs",
    "DigitalElevationModel",
    "slope_percent",
    "waterway",
    "assess_parcel_buffers",
    "analyze_noise",
    "analyze_viewshed",
    "combine_overlay_results",
    "compute_constraint_scores",
    "load_usgs_dem",
    "load_nhd_waterways",
    "compute_urban_accessibility",
]


def compute_urban_accessibility(
    origin_points: list[tuple[float, float]],
    amenities_gdf: "gpd.GeoDataFrame",
    bbox: tuple[float, float, float, float],
    network_type: str = "walk",
) -> "gpd.GeoDataFrame":
    """Compute urban accessibility metrics for origin points.

    This function combines isochrone computation and amenity analysis
    to produce standardized market_urban fields.

    Args:
        origin_points: List of (lat, lon) coordinate tuples
        amenities_gdf: GeoDataFrame with amenity points
        bbox: Bounding box for street network (west, south, east, north)
        network_type: OSM network type ("walk", "bike", "drive")

    Returns:
        GeoDataFrame with accessibility metrics for each origin point
    """
    # Convert origin points to Point objects
    from shapely.geometry import Point

    origin_points_geom = [
        Point(lon, lat) for lat, lon in origin_points
    ]  # Note: Point(lon, lat) for shapely

    # Compute isochrones
    isochrones_gdf = compute_isochrones(
        origin_points=origin_points_geom,
        mode="walk",
        max_time_minutes=15,
        bbox=bbox,
        network_type=network_type,
    )

    # Count amenities within isochrones
    accessibility_gdf = count_amenities_in_isochrones(isochrones_gdf, amenities_gdf)

    # Rename columns to match market_urban schema
    column_mapping = {
        "grocery_count": "walk_15_grocery_ct",
        "pharmacy_count": "walk_15_pharmacy_ct",
        "healthcare_count": "walk_15_healthcare_ct",
        "education_count": "walk_15_education_ct",
        "transit_count": "walk_15_transit_ct",
        "recreation_count": "walk_15_recreation_ct",
        "shopping_count": "walk_15_shopping_ct",
        "dining_count": "walk_15_dining_ct",
        "banking_count": "walk_15_banking_ct",
        "services_count": "walk_15_services_ct",
        "total_amenities": "walk_15_total_ct",
    }

    for old_col, new_col in column_mapping.items():
        if old_col in accessibility_gdf.columns:
            accessibility_gdf = accessibility_gdf.rename(columns={old_col: new_col})

    return accessibility_gdf
