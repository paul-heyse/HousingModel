"""Digital elevation model helpers for terrain analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import numpy as np

try:  # pragma: no cover - optional acceleration in Shapely 2.0+
    from shapely import contains_xy  # type: ignore
except ImportError:  # pragma: no cover
    contains_xy = None  # type: ignore

try:  # pragma: no cover - Shapely <2 fallback
    from shapely import vectorized  # type: ignore
except ImportError:  # pragma: no cover
    vectorized = None  # type: ignore

from shapely.geometry import Point


@dataclass(slots=True)
class DigitalElevationModel:
    """Simple in-memory representation of a north-up digital elevation model.

    The DEM stores elevation values on a regular grid alongside the origin and
    pixel resolution so we can derive slope, sample geometries, and compute
    statistics without binding to a specific raster backend.  The grid is
    assumed to be north-up with the origin located at the upper-left corner of
    the first pixel.
    """

    values: np.ndarray
    origin: Tuple[float, float]
    pixel_size: Tuple[float, float]
    crs: str = "EPSG:4326"
    nodata: float | None = None
    _centers_cache: tuple[np.ndarray, np.ndarray] | None = field(
        default=None, init=False, repr=False
    )

    def __post_init__(self) -> None:
        array = np.asarray(self.values, dtype=float)
        if array.ndim != 2:
            raise ValueError("DEM values must be a 2D array")
        if array.size == 0:
            raise ValueError("DEM values may not be empty")
        self.values = array
        if self.pixel_size[0] <= 0 or self.pixel_size[1] <= 0:
            raise ValueError("Pixel sizes must be positive")

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the raster shape as (rows, cols)."""

        return self.values.shape

    @property
    def valid_mask(self) -> np.ndarray:
        """Boolean mask indicating which cells contain valid elevation data."""

        if self.nodata is None:
            return ~np.isnan(self.values)
        return (~np.isnan(self.values)) & (self.values != self.nodata)

    def cell_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return arrays of x/y coordinates for each cell centre."""

        if self._centers_cache is not None:
            return self._centers_cache

        rows, cols = self.shape
        row_indices, col_indices = np.indices((rows, cols), dtype=float)
        x0, y0 = self.origin
        x_size, y_size = self.pixel_size

        xs = x0 + (col_indices + 0.5) * x_size
        ys = y0 - (row_indices + 0.5) * y_size
        self._centers_cache = (xs, ys)
        return xs, ys

    def _masked_values(self) -> np.ndarray:
        """Return a copy of the DEM with invalid cells set to NaN."""

        data = self.values.astype(float)
        mask = ~self.valid_mask
        if mask.any():
            data = data.copy()
            data[mask] = np.nan
        return data

    def slope_components(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return dz/dx and dz/dy components using central differences."""

        grid = self._masked_values()
        y_spacing = self.pixel_size[1]
        x_spacing = self.pixel_size[0]

        # numpy.gradient handles NaNs by propagating them which is what we want
        d_dy, d_dx = np.gradient(grid, y_spacing, x_spacing)
        return d_dx, d_dy

    def slope_ratio(self) -> np.ndarray:
        """Return slope as rise/run ratio for each cell."""

        d_dx, d_dy = self.slope_components()
        slope = np.sqrt(d_dx**2 + d_dy**2)
        return slope

    def slope_percent_grid(self) -> np.ndarray:
        """Return slope expressed as percent grade for each cell."""

        slope = self.slope_ratio()
        return slope * 100.0

    def slope_degrees_grid(self) -> np.ndarray:
        """Return slope expressed in degrees for each cell."""

        slope = self.slope_ratio()
        return np.degrees(np.arctan(slope))

    def mask_geometry(self, geometry) -> np.ndarray:
        """Return a boolean mask selecting cells whose centres intersect geometry."""

        if geometry is None:
            raise ValueError("Geometry is required for masking")

        xs, ys = self.cell_centers()

        if contains_xy is not None:
            mask = contains_xy(geometry, xs, ys)
        elif vectorized is not None:
            mask = vectorized.contains(geometry, xs, ys)
        else:
            # Fall back to per-point evaluation for older Shapely versions
            mask = np.zeros_like(xs, dtype=bool)
            for idx, (x_val, y_val) in enumerate(zip(xs.flat, ys.flat)):
                if geometry.contains(Point(x_val, y_val)):
                    mask.flat[idx] = True
        return mask

    def coverage_ratio(self, geometry) -> float:
        """Return the ratio of valid DEM cells intersecting the geometry."""

        parcel_mask = self.mask_geometry(geometry)
        if not parcel_mask.any():
            return 0.0
        valid = self.valid_mask & parcel_mask
        return float(valid.sum()) / float(parcel_mask.sum())

    def clip(self, geometry) -> np.ndarray:
        """Return elevation values intersecting the geometry as a 1D array."""

        parcel_mask = self.mask_geometry(geometry)
        if not parcel_mask.any():
            return np.array([], dtype=float)
        valid = self.valid_mask & parcel_mask
        data = self._masked_values()
        return data[valid]

    def quality_report(self) -> Dict[str, float | tuple[float, float] | str]:
        """Return basic quality metrics for the DEM."""

        total_cells = float(self.values.size)
        valid_cells = float(self.valid_mask.sum())
        return {
            "crs": self.crs,
            "pixel_size": self.pixel_size,
            "valid_ratio": valid_cells / total_cells,
        }
