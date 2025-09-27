"""Terrain analysis toolkit built on top of geospatial primitives."""

from .analysis import SlopeAnalysisError, SlopeStatistics, slope_percent
from .buffers import assess_parcel_buffers, waterway
from .dem import DigitalElevationModel
from .overlay import analyze_noise, analyze_viewshed, combine_overlay_results
from .scoring import compute_constraint_scores
from .sources import load_nhd_waterways, load_usgs_dem

__all__ = [
    "DigitalElevationModel",
    "SlopeStatistics",
    "SlopeAnalysisError",
    "slope_percent",
    "waterway",
    "assess_parcel_buffers",
    "analyze_noise",
    "analyze_viewshed",
    "combine_overlay_results",
    "compute_constraint_scores",
    "load_usgs_dem",
    "load_nhd_waterways",
]
