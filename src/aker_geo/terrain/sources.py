"""Static data source helpers for terrain analysis."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from .dem import DigitalElevationModel


def load_usgs_dem(path: str | Path) -> DigitalElevationModel:
    """Load a USGS DEM file into an in-memory :class:`DigitalElevationModel`.

    The function uses :mod:`rasterio` when available and raises a descriptive
    error when the dependency is missing.
    """

    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("rasterio is required to load USGS DEM data") from exc

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with rasterio.open(path) as src:
        array = src.read(1).astype(float)
        transform = src.transform
        pixel_size = (transform.a, abs(transform.e))
        origin = (transform.c, transform.f)
        crs = src.crs.to_string() if src.crs else "EPSG:4326"
        nodata = src.nodata

    return DigitalElevationModel(
        array, origin=origin, pixel_size=pixel_size, crs=crs, nodata=nodata
    )


def load_nhd_waterways(path: str | Path, *, layer: str | None = None) -> gpd.GeoDataFrame:
    """Load NHD waterway features and normalise attribute columns."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    waterways = gpd.read_file(path, layer=layer)
    if "feature_type" not in waterways.columns and "FType" in waterways.columns:
        waterways = waterways.rename(columns={"FType": "feature_type"})
    if waterways.crs is None:
        waterways.set_crs("EPSG:4269", inplace=True)
    return waterways
