"""Overlay analysis utilities for noise and viewshed constraints."""

from __future__ import annotations

from typing import Dict, List, Mapping

import geopandas as gpd
import pandas as pd

TARGET_AREA_CRS = "EPSG:3857"


def _prepare_layers(
    parcels: gpd.GeoDataFrame,
    overlays: gpd.GeoDataFrame,
    target_crs: str = TARGET_AREA_CRS,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if not isinstance(parcels, gpd.GeoDataFrame):
        raise TypeError("parcels must be a GeoDataFrame")
    if not isinstance(overlays, gpd.GeoDataFrame):
        raise TypeError("overlays must be a GeoDataFrame")
    if overlays.empty:
        raise ValueError("overlays GeoDataFrame is empty")
    if parcels.geometry.isna().any():
        raise ValueError("parcels contain missing geometries")
    if overlays.geometry.isna().any():
        raise ValueError("overlays contain missing geometries")
    if overlays.crs is None:
        raise ValueError("Overlays must define a CRS")
    if parcels.crs is None:
        raise ValueError("Parcels must define a CRS")

    parcels_proj = parcels.to_crs(target_crs)
    overlays_proj = overlays.to_crs(target_crs)
    return parcels_proj, overlays_proj


def _analyse_overlay(
    parcels: gpd.GeoDataFrame,
    overlays: gpd.GeoDataFrame,
    *,
    value_column: str,
    prefix: str,
    source_column: str = "source",
) -> pd.DataFrame:
    parcels_proj, overlays_proj = _prepare_layers(parcels, overlays)

    results: Dict[int, Dict[str, object]] = {}

    for idx, parcel_geom in parcels_proj.geometry.items():
        total_area = parcel_geom.area
        exposure = 0.0
        impacted_pct = 0.0
        contributing_sources: List[str] = []
        impact_breakdown: Dict[str, float] = {}

        for overlay_row in overlays_proj.itertuples():
            overlay_geom = overlay_row.geometry
            intersection = parcel_geom.intersection(overlay_geom)
            if intersection.is_empty or total_area == 0.0:
                continue

            area_fraction = intersection.area / total_area
            impacted_pct += area_fraction * 100.0
            value = getattr(overlay_row, value_column, None)
            if value is None:
                value = 1.0
            exposure += area_fraction * float(value)
            source = getattr(overlay_row, source_column, None)
            if source:
                contributing_sources.append(str(source))
            impact_breakdown[str(getattr(overlay_row, value_column, "unknown"))] = (
                area_fraction * 100.0
            )

        results[idx] = {
            f"{prefix}_exposure": float(exposure),
            f"{prefix}_overlay_pct": float(min(impacted_pct, 100.0)),
            f"{prefix}_sources": sorted(set(contributing_sources)),
            f"{prefix}_impact_breakdown": impact_breakdown,
        }

    return pd.DataFrame.from_dict(results, orient="index")


def analyze_noise(
    parcels: gpd.GeoDataFrame,
    noise_overlays: gpd.GeoDataFrame,
    *,
    value_column: str = "decibel",
    source_column: str = "source",
) -> pd.DataFrame:
    """Calculate noise exposure metrics for each parcel."""

    return _analyse_overlay(
        parcels,
        noise_overlays,
        value_column=value_column,
        prefix="noise",
        source_column=source_column,
    )


def analyze_viewshed(
    parcels: gpd.GeoDataFrame,
    viewshed_overlays: gpd.GeoDataFrame,
    *,
    value_column: str = "impact",
    source_column: str = "source",
) -> pd.DataFrame:
    """Calculate viewshed restriction metrics for each parcel."""

    return _analyse_overlay(
        parcels,
        viewshed_overlays,
        value_column=value_column,
        prefix="viewshed",
        source_column=source_column,
    )


def combine_overlay_results(
    parcels: gpd.GeoDataFrame,
    *,
    noise: pd.DataFrame | None = None,
    viewshed: pd.DataFrame | None = None,
    additional: Mapping[str, pd.DataFrame] | None = None,
) -> gpd.GeoDataFrame:
    """Combine overlay analysis outputs and derive unified constraint scoring."""

    frames: List[pd.DataFrame] = []
    if noise is not None:
        frames.append(noise)
    if viewshed is not None:
        frames.append(viewshed)
    if additional:
        frames.extend(additional.values())

    if frames:
        combined = pd.concat(frames, axis=1)
    else:
        combined = pd.DataFrame(index=parcels.index)

    combined = combined.reindex(parcels.index)

    # Simple scoring heuristic: weight noise and viewshed equally if present
    noise_pct = combined.get("noise_overlay_pct", pd.Series(0.0, index=parcels.index))
    viewshed_pct = combined.get("viewshed_overlay_pct", pd.Series(0.0, index=parcels.index))

    overlay_constraint_score = (noise_pct.fillna(0.0) + viewshed_pct.fillna(0.0)) / 2.0
    combined["overlay_constraint_score"] = overlay_constraint_score.clip(upper=100.0)

    return parcels.join(combined)
