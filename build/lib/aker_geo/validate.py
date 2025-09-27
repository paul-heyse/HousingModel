"""Geometry validation and correction utilities."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

import geopandas as gpd
import pandas as pd
from shapely.validation import explain_validity

from .crs import STORAGE_CRS, UI_CRS, detect_crs_from_geometry


class GeometryValidationResult:
    """Container for geometry validation results."""

    def __init__(
        self,
        total_geometries: int,
        valid_geometries: int,
        invalid_geometries: int,
        corrected_geometries: int = 0,
        validation_errors: Optional[List[Dict[str, any]]] = None,
    ):
        self.total_geometries = total_geometries
        self.valid_geometries = valid_geometries
        self.invalid_geometries = invalid_geometries
        self.corrected_geometries = corrected_geometries
        self.validation_errors = validation_errors or []

    @property
    def validity_rate(self) -> float:
        """Percentage of valid geometries."""
        return self.valid_geometries / self.total_geometries if self.total_geometries > 0 else 0.0

    @property
    def correction_rate(self) -> float:
        """Percentage of geometries that were corrected."""
        return (
            self.corrected_geometries / self.total_geometries if self.total_geometries > 0 else 0.0
        )

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "total_geometries": self.total_geometries,
            "valid_geometries": self.valid_geometries,
            "invalid_geometries": self.invalid_geometries,
            "corrected_geometries": self.corrected_geometries,
            "validity_rate": self.validity_rate,
            "correction_rate": self.correction_rate,
            "validation_errors": self.validation_errors,
        }


def validate_geometry(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> GeometryValidationResult:
    """Validate geometry data for spatial integrity.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        GeometryValidationResult with validation statistics and errors
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        if "geometry" not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")
        gdf = gpd.GeoDataFrame(gdf)

    total_geometries = len(gdf)
    valid_geometries = 0
    invalid_geometries = 0
    corrected_geometries = 0
    validation_errors = []

    for idx, row in gdf.iterrows():
        geometry = row.geometry
        if geometry is None:
            invalid_geometries += 1
            validation_errors.append(
                {"index": idx, "error_type": "null_geometry", "message": "Geometry is None"}
            )
            continue

        # Check geometry validity
        is_valid = geometry.is_valid

        if not is_valid:
            invalid_geometries += 1

            # Get detailed validation error
            try:
                error_msg = explain_validity(geometry)
            except Exception:
                error_msg = "Unknown validation error"

            validation_errors.append(
                {
                    "index": idx,
                    "error_type": "invalid_geometry",
                    "message": error_msg,
                    "geometry_type": geometry.geom_type,
                }
            )

            # Try to correct the geometry
            try:
                corrected = geometry.buffer(0)  # Simple correction attempt
                if corrected.is_valid:
                    corrected_geometries += 1
                    # Note: In practice, we'd update the DataFrame here
            except Exception:
                pass  # Correction failed
        else:
            valid_geometries += 1

    return GeometryValidationResult(
        total_geometries=total_geometries,
        valid_geometries=valid_geometries,
        invalid_geometries=invalid_geometries,
        corrected_geometries=corrected_geometries,
        validation_errors=validation_errors,
    )


def validate_crs(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> Dict[str, any]:
    """Validate coordinate reference system information.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        Dictionary with CRS validation results
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        if "geometry" not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")
        gdf = gpd.GeoDataFrame(gdf)

    current_crs = gdf.crs
    validation_result = {
        "has_crs": current_crs is not None,
        "crs_name": str(current_crs) if current_crs else None,
        "is_storage_crs": False,
        "is_ui_crs": False,
        "detected_crs": None,
    }

    if current_crs:
        validation_result["is_storage_crs"] = str(current_crs) == STORAGE_CRS
        validation_result["is_ui_crs"] = str(current_crs) == UI_CRS

        # Try to detect CRS from geometry if not set
        if len(gdf) > 0:
            sample_geometry = gdf.geometry.iloc[0]
            detected_crs = detect_crs_from_geometry(sample_geometry)
            validation_result["detected_crs"] = detected_crs

    return validation_result


def correct_geometry(geometry) -> Optional[any]:
    """Attempt to correct an invalid geometry.

    Args:
        geometry: Shapely geometry object

    Returns:
        Corrected geometry or None if correction fails
    """
    if geometry is None or geometry.is_valid:
        return geometry

    try:
        # Try buffer(0) correction
        corrected = geometry.buffer(0)
        if corrected.is_valid:
            return corrected
    except Exception:
        pass

    try:
        # Try make_valid if available (Shapely 2.0+)
        if hasattr(geometry, "make_valid"):
            corrected = geometry.make_valid()
            if corrected.is_valid:
                return corrected
    except Exception:
        pass

    # Try unary_union for self-intersecting polygons
    try:
        if geometry.geom_type in ["Polygon", "MultiPolygon"]:
            from shapely.ops import unary_union

            corrected = unary_union([geometry])
            if corrected.is_valid:
                return corrected
    except Exception:
        pass

    return None


def validate_geometry_types(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> Dict[str, any]:
    """Validate geometry types in the dataset.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        Dictionary with geometry type validation results
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        if "geometry" not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")
        gdf = gpd.GeoDataFrame(gdf)

    geometry_types = gdf.geometry.geom_type.value_counts()
    total_geometries = len(gdf)

    # Check for mixed geometry types
    has_mixed_types = len(geometry_types) > 1

    # Check for empty geometries
    empty_geometries = gdf.geometry.is_empty.sum()

    # Check for null geometries
    null_geometries = gdf.geometry.isna().sum()

    return {
        "geometry_types": geometry_types.to_dict(),
        "total_geometries": total_geometries,
        "has_mixed_types": has_mixed_types,
        "empty_geometries": int(empty_geometries),
        "null_geometries": int(null_geometries),
        "valid_geometries": total_geometries - int(empty_geometries) - int(null_geometries),
    }


def validate_spatial_bounds(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> Dict[str, any]:
    """Validate spatial bounds and coverage.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        Dictionary with spatial bounds validation results
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        if "geometry" not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")
        gdf = gpd.GeoDataFrame(gdf)

    try:
        bounds = gdf.total_bounds
        return {
            "has_bounds": True,
            "min_x": float(bounds[0]),
            "min_y": float(bounds[1]),
            "max_x": float(bounds[2]),
            "max_y": float(bounds[3]),
            "width": float(bounds[2] - bounds[0]),
            "height": float(bounds[3] - bounds[1]),
        }
    except Exception as e:
        return {"has_bounds": False, "error": str(e)}


def validate_postgis_compatibility(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> Dict[str, any]:
    """Validate compatibility with PostGIS geometry storage.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        Dictionary with PostGIS compatibility validation results
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        if "geometry" not in gdf.columns:
            raise ValueError("DataFrame must have 'geometry' column or be a GeoDataFrame")
        gdf = gpd.GeoDataFrame(gdf)

    compatibility = {
        "crs_compatible": True,
        "geometry_types_supported": True,
        "has_srid": gdf.crs is not None,
        "srid_value": str(gdf.crs) if gdf.crs else None,
        "geometry_types": [],
    }

    # Check geometry types
    geometry_types = gdf.geometry.geom_type.unique()
    compatibility["geometry_types"] = list(geometry_types)

    # PostGIS supports: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
    supported_types = {
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    }

    unsupported_types = set(geometry_types) - supported_types
    if unsupported_types:
        compatibility["geometry_types_supported"] = False
        compatibility["unsupported_types"] = list(unsupported_types)

    # Check CRS compatibility
    if gdf.crs and str(gdf.crs) not in [STORAGE_CRS, UI_CRS]:
        compatibility["crs_compatible"] = False
        compatibility["recommended_crs"] = STORAGE_CRS

    return compatibility


def comprehensive_geometry_validation(gdf: Union[gpd.GeoDataFrame, pd.DataFrame]) -> Dict[str, any]:
    """Perform comprehensive geometry validation.

    Args:
        gdf: GeoDataFrame or DataFrame with geometry column

    Returns:
        Dictionary with comprehensive validation results
    """
    results = {
        "geometry_validation": None,
        "crs_validation": None,
        "geometry_types": None,
        "spatial_bounds": None,
        "postgis_compatibility": None,
        "summary": {},
    }

    try:
        # Geometry validation
        results["geometry_validation"] = validate_geometry(gdf).to_dict()

        # CRS validation
        results["crs_validation"] = validate_crs(gdf)

        # Geometry types validation
        results["geometry_types"] = validate_geometry_types(gdf)

        # Spatial bounds validation
        results["spatial_bounds"] = validate_spatial_bounds(gdf)

        # PostGIS compatibility
        results["postgis_compatibility"] = validate_postgis_compatibility(gdf)

        # Summary statistics
        total_geoms = results["geometry_validation"]["total_geometries"]
        valid_geoms = results["geometry_validation"]["valid_geometries"]
        results["summary"] = {
            "total_geometries": total_geoms,
            "valid_geometries": valid_geoms,
            "invalid_geometries": total_geoms - valid_geoms,
            "validity_rate": valid_geoms / total_geoms if total_geoms > 0 else 0,
            "crs_detected": results["crs_validation"]["has_crs"],
            "spatial_bounds_available": results["spatial_bounds"]["has_bounds"],
            "postgis_compatible": results["postgis_compatibility"]["crs_compatible"]
            and results["postgis_compatibility"]["geometry_types_supported"],
        }

    except Exception as e:
        results["error"] = str(e)

    return results
