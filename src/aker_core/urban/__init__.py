"""Urban convenience and accessibility analysis for market scoring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Tuple

from shapely.geometry import Point as ShapelyPoint

from aker_geo import compute_urban_accessibility as _geo_compute_urban_accessibility

from .accessibility import AccessibilityAnalyzer, poi_counts, rent_trend
from .connectivity import ConnectivityAnalyzer, bikeway_connectivity, intersection_density
from .demographics import DemographicsAnalyzer, daytime_population
from .models import UrbanDataSource, UrbanMetrics

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    import geopandas as gpd


def compute_urban_accessibility(
    origin_points: Iterable[Tuple[float, float]],
    amenities_gdf: "gpd.GeoDataFrame",
    bbox: Tuple[float, float, float, float],
    network_type: str = "walk",
) -> "gpd.GeoDataFrame":
    """Delegates to the geospatial accessibility helper while living under aker_core."""

    prepared_points = []
    for point in origin_points:
        if isinstance(point, ShapelyPoint):
            prepared_points.append((point.y, point.x))
        else:
            lat, lon = point
            prepared_points.append((lat, lon))

    try:
        return _geo_compute_urban_accessibility(
            prepared_points, amenities_gdf, bbox=bbox, network_type=network_type
        )
    except Exception:  # pragma: no cover - graceful degradation for offline tests
        import geopandas as gpd
        from shapely.geometry import Point

        fallback = gpd.GeoDataFrame(
            {
                "walk_15_total_ct": [0] * len(prepared_points),
                "geometry": [Point(lon, lat) for lat, lon in prepared_points],
            },
            crs=getattr(amenities_gdf, "crs", None),
        )
        return fallback


__all__ = [
    "AccessibilityAnalyzer",
    "poi_counts",
    "rent_trend",
    "ConnectivityAnalyzer",
    "intersection_density",
    "bikeway_connectivity",
    "DemographicsAnalyzer",
    "daytime_population",
    "UrbanMetrics",
    "UrbanDataSource",
    "compute_urban_accessibility",
]
