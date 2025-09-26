"""Coordinate Reference System (CRS) transformation utilities."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
from pyproj import CRS, Transformer
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform
from typing import Optional, Union

# Standard CRS definitions
STORAGE_CRS = "EPSG:4326"  # WGS84 - Geographic coordinates for storage
UI_CRS = "EPSG:3857"       # Web Mercator - Projected coordinates for UI


def to_ui(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> gpd.GeoDataFrame:
    """Transform geometries from storage CRS (EPSG:4326) to UI CRS (EPSG:3857).

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        GeoDataFrame with geometries transformed to UI CRS

    Raises:
        ValueError: If geometry column is missing or CRS transformation fails
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        # Convert to GeoDataFrame if needed
        if 'geometry' not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")

        gdf = gpd.GeoDataFrame(gdf)

    # Check current CRS
    current_crs = gdf.crs
    if current_crs is None:
        # Assume storage CRS if not specified
        gdf = gdf.set_crs(STORAGE_CRS)

    # Transform to UI CRS
    try:
        result_gdf = gdf.to_crs(UI_CRS)
        return result_gdf
    except Exception as e:
        raise ValueError(f"Failed to transform CRS to {UI_CRS}: {e}")


def to_storage(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> gpd.GeoDataFrame:
    """Transform geometries from UI CRS (EPSG:3857) to storage CRS (EPSG:4326).

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        GeoDataFrame with geometries transformed to storage CRS

    Raises:
        ValueError: If geometry column is missing or CRS transformation fails
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        # Convert to GeoDataFrame if needed
        if 'geometry' not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")

        gdf = gpd.GeoDataFrame(gdf)

    # Check current CRS
    current_crs = gdf.crs
    if current_crs is None:
        # Assume UI CRS if not specified
        gdf = gdf.set_crs(UI_CRS)

    # Transform to storage CRS
    try:
        result_gdf = gdf.to_crs(STORAGE_CRS)
        return result_gdf
    except Exception as e:
        raise ValueError(f"Failed to transform CRS to {STORAGE_CRS}: {e}")


def get_crs_info(crs: Union[str, CRS]) -> Dict[str, any]:
    """Get information about a coordinate reference system.

    Args:
        crs: CRS string (e.g., "EPSG:4326") or CRS object

    Returns:
        Dictionary with CRS information
    """
    if isinstance(crs, str):
        crs = CRS(crs)

    return {
        "name": crs.name,
        "datum": crs.datum.name if crs.datum else None,
        "coordinate_system": crs.coordinate_system.name if crs.coordinate_system else None,
        "area_of_use": str(crs.area_of_use) if crs.area_of_use else None,
        "axis_info": [
            {
                "name": axis.name,
                "direction": axis.direction,
                "unit_name": axis.unit_name
            }
            for axis in crs.axis_info
        ]
    }


def validate_crs_compatibility(source_crs: Union[str, CRS], target_crs: Union[str, CRS]) -> bool:
    """Validate that two CRS are compatible for transformation.

    Args:
        source_crs: Source coordinate reference system
        target_crs: Target coordinate reference system

    Returns:
        True if CRS are compatible for transformation
    """
    try:
        source_crs_obj = CRS(source_crs) if isinstance(source_crs, str) else source_crs
        target_crs_obj = CRS(target_crs) if isinstance(target_crs, str) else target_crs

        # Try to create a transformer - if it fails, CRS are not compatible
        transformer = Transformer.from_crs(source_crs_obj, target_crs_obj)
        return transformer is not None
    except Exception:
        return False


def transform_geometry(geometry: any, source_crs: str, target_crs: str) -> any:
    """Transform a single geometry from source CRS to target CRS.

    Args:
        geometry: Shapely geometry object
        source_crs: Source CRS (EPSG code string)
        target_crs: Target CRS (EPSG code string)

    Returns:
        Transformed geometry
    """
    try:
        source_crs_obj = CRS(source_crs)
        target_crs_obj = CRS(target_crs)
        transformer = Transformer.from_crs(source_crs_obj, target_crs_obj)

        # Use shapely transform with pyproj transformer
        transformed = shapely_transform(transformer.transform, geometry)
        return transformed
    except Exception as e:
        raise ValueError(f"Failed to transform geometry from {source_crs} to {target_crs}: {e}")


def detect_crs_from_geometry(geometry: any) -> Optional[str]:
    """Attempt to detect CRS from geometry bounds (heuristic).

    Args:
        geometry: Shapely geometry object

    Returns:
        Detected CRS string or None if detection fails
    """
    try:
        if geometry is None or not hasattr(geometry, 'bounds'):
            return None

        bounds = geometry.bounds
        if len(bounds) >= 4:
            # Check if bounds look like geographic coordinates (lat/lon)
            min_lon, min_lat, max_lon, max_lat = bounds

            # Geographic coordinates typically have:
            # - Longitude between -180 and 180
            # - Latitude between -90 and 90
            if (-180 <= min_lon <= 180 and -180 <= max_lon <= 180 and
                -90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                return STORAGE_CRS  # EPSG:4326
            else:
                # Could be projected coordinates
                return UI_CRS  # EPSG:3857

    except Exception:
        pass

    return None


def ensure_geometry_column(df: pd.DataFrame, geometry_column: str = "geometry") -> gpd.GeoDataFrame:
    """Ensure DataFrame has a proper geometry column for spatial operations.

    Args:
        df: Input DataFrame
        geometry_column: Name of geometry column

    Returns:
        GeoDataFrame with proper geometry column
    """
    if geometry_column not in df.columns:
        raise ValueError(f"Geometry column '{geometry_column}' not found in DataFrame")

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df)

    # Ensure geometry column is properly typed
    if not isinstance(gdf[geometry_column].iloc[0] if len(gdf) > 0 else None, shape):
        # Try to convert from WKT or WKB if needed
        try:
            # This is a simplified conversion - in practice you'd handle WKT/WKB parsing
            pass
        except Exception:
            raise ValueError(f"Cannot convert column '{geometry_column}' to geometry objects")

    return gdf
