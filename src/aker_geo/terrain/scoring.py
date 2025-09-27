"""Constraint scoring utilities for market supply integration."""

from __future__ import annotations

from typing import Mapping

import geopandas as gpd
import numpy as np
import pandas as pd

SLOPE_SEVERITY_WEIGHTS: Mapping[str, float] = {
    "flat": 0.0,
    "moderate": 15.0,
    "steep": 35.0,
    "extreme": 55.0,
}

DEFAULT_WEIGHTS: Mapping[str, float] = {
    "slope": 0.4,
    "buffer": 0.3,
    "overlay": 0.3,
}


def compute_constraint_scores(
    parcels: gpd.GeoDataFrame,
    *,
    slope: gpd.GeoDataFrame | None = None,
    buffers: gpd.GeoDataFrame | None = None,
    overlays: gpd.GeoDataFrame | None = None,
    weights: Mapping[str, float] | None = None,
) -> gpd.GeoDataFrame:
    """Combine slope, buffer, and overlay analyses into unified constraint scores."""

    if weights is None:
        weights = DEFAULT_WEIGHTS

    result = parcels.copy()

    if slope is not None:
        result = result.join(
            slope[
                [
                    "slope_constrained_area_pct",
                    "slope_primary_severity",
                    "slope_confidence",
                ]
            ],
            rsuffix="_slope",
        )
        result["slope_pct"] = result["slope_constrained_area_pct"].fillna(0.0)
        severity_series = result["slope_primary_severity"].fillna("flat")
        severity_weight = severity_series.map(SLOPE_SEVERITY_WEIGHTS).fillna(0.0)
        slope_score = np.clip(result["slope_pct"] + severity_weight, 0.0, 100.0)
    else:
        slope_score = pd.Series(0.0, index=result.index)
        result["slope_pct"] = 0.0

    if buffers is not None:
        result = result.join(
            buffers[
                [
                    "buffer_impacted_pct",
                    "buffer_severity",
                ]
            ],
            rsuffix="_buffer",
        )
        result["buffer_pct"] = result["buffer_impacted_pct"].fillna(0.0)
        buffer_severity = result["buffer_severity"].fillna("none")
        buffer_weight = buffer_severity.map(
            {"none": 0.0, "low": 10.0, "medium": 25.0, "high": 40.0}
        ).fillna(0.0)
        buffer_score = np.clip(result["buffer_pct"] + buffer_weight, 0.0, 100.0)
    else:
        buffer_score = pd.Series(0.0, index=result.index)
        result["buffer_pct"] = 0.0

    if overlays is not None:
        result = result.join(overlays, rsuffix="_overlay")
        overlay_score = overlays.get(
            "overlay_constraint_score", pd.Series(0.0, index=result.index)
        ).fillna(0.0)
        result["noise_overlay_pct"] = overlays.get(
            "noise_overlay_pct", pd.Series(0.0, index=result.index)
        ).fillna(0.0)
        result["protected_pct"] = overlays.get(
            "viewshed_overlay_pct", pd.Series(0.0, index=result.index)
        ).fillna(0.0)
    else:
        overlay_score = pd.Series(0.0, index=result.index)
        result["noise_overlay_pct"] = 0.0
        result["protected_pct"] = 0.0

    slope_weight = weights.get("slope", 0.0)
    buffer_weight = weights.get("buffer", 0.0)
    overlay_weight = weights.get("overlay", 0.0)

    total_weight = slope_weight + buffer_weight + overlay_weight
    if total_weight == 0:
        total_weight = 1.0

    combined_score = (
        slope_score * slope_weight + buffer_score * buffer_weight + overlay_score * overlay_weight
    ) / total_weight

    result["constraint_score"] = combined_score.clip(0.0, 100.0)
    result["constraint_details"] = [
        {
            "slope_score": float(slope_score.loc[idx]),
            "buffer_score": float(buffer_score.loc[idx]),
            "overlay_score": float(overlay_score.loc[idx]),
            "weights": dict(weights),
        }
        for idx in result.index
    ]

    return result
