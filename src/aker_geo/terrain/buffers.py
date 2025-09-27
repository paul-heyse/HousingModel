"""Waterway buffer generation and assessment utilities."""

from __future__ import annotations

from typing import Dict, List, Mapping, Sequence

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

FT_TO_M = 0.3048


def _build_distance_sequence(
    distance_range: Sequence[float] | Mapping | float,
    *,
    step: float,
) -> List[float]:
    if isinstance(distance_range, Mapping):
        distances = list(distance_range.values())
    elif isinstance(distance_range, Sequence) and len(distance_range) > 0:
        if len(distance_range) == 2 and all(
            isinstance(val, (int, float)) for val in distance_range
        ):
            start, end = distance_range
            if end < start:
                raise ValueError("distance_range end must be >= start")
            distances = list(np.arange(start, end + step, step))
        else:
            distances = list(distance_range)
    else:
        distances = [float(distance_range)]
    return sorted(set(float(d) for d in distances))


def waterway(
    waterways: gpd.GeoDataFrame,
    distance_range: Sequence[float] | float = (100.0, 300.0),
    *,
    step: float = 100.0,
    target_crs: str = "EPSG:3857",
) -> gpd.GeoDataFrame:
    """Generate buffer polygons around waterways for constraint analysis.

    The function supports generating multiple buffer distances (typically 100–300
    feet) and returns a GeoDataFrame containing a buffer per source feature and
    distance.
    """

    if not isinstance(waterways, gpd.GeoDataFrame):
        raise TypeError("waterways must be a GeoDataFrame")
    if waterways.empty:
        raise ValueError("waterways GeoDataFrame is empty")
    if waterways.crs is None:
        raise ValueError("waterways GeoDataFrame must define a CRS")

    distances_ft = _build_distance_sequence(distance_range, step=step)
    if not distances_ft:
        raise ValueError("No buffer distances were derived")

    working = waterways.to_crs(target_crs)

    records: List[Dict[str, object]] = []
    for idx, row in working.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        feature_type = row.get("feature_type")
        if feature_type is None:
            feature_type = row.get("FType") or row.get("ftype")
        if isinstance(feature_type, str):
            feature_type = feature_type.lower()
        for distance_ft in distances_ft:
            distance_m = distance_ft * FT_TO_M
            buffered = geom.buffer(distance_m)
            if buffered.is_empty:
                continue
            records.append(
                {
                    "source_id": idx,
                    "distance_ft": float(distance_ft),
                    "distance_m": float(distance_m),
                    "feature_type": feature_type,
                    "geometry": buffered,
                }
            )

    if not records:
        return gpd.GeoDataFrame(
            columns=["source_id", "distance_ft", "distance_m", "feature_type", "geometry"],
            crs=target_crs,
        )

    buffers = gpd.GeoDataFrame(records, crs=target_crs)
    return buffers


def assess_parcel_buffers(
    parcels: gpd.GeoDataFrame,
    buffer_polygons: gpd.GeoDataFrame,
    *,
    severity_breaks: Mapping[str, float] | None = None,
) -> gpd.GeoDataFrame:
    """Calculate parcel impacts from generated waterway buffer polygons."""

    if not isinstance(parcels, gpd.GeoDataFrame):
        raise TypeError("parcels must be a GeoDataFrame")
    if parcels.geometry.isna().any():
        raise ValueError("parcels contain missing geometries")
    if buffer_polygons.empty:
        empty_cols = {
            "buffer_impacted_pct": [],
            "buffer_distance_impacts": [],
            "buffer_severity": [],
            "buffer_feature_types": [],
        }
        return parcels.join(gpd.GeoDataFrame(empty_cols, index=parcels.index))

    if buffer_polygons.crs is None:
        raise ValueError("buffer_polygons must define a CRS")

    target_crs = buffer_polygons.crs
    parcels_proj = parcels.to_crs(target_crs)

    # Pre-compute unary unions per buffer distance to avoid repeated dissolves
    distance_groups: Dict[float, object] = {}
    for distance_ft, group in buffer_polygons.groupby("distance_ft"):
        distance_groups[float(distance_ft)] = unary_union(group.geometry)

    combined_union = unary_union(buffer_polygons.geometry)

    if severity_breaks is None:
        severity_breaks = {"none": 0.0, "low": 5.0, "medium": 20.0, "high": 40.0}
    severity_sequence = sorted(severity_breaks.items(), key=lambda item: item[1])

    records: Dict[int, Dict[str, object]] = {}

    for idx, geom in parcels_proj.geometry.items():
        if geom is None or geom.is_empty:
            records[idx] = {
                "buffer_impacted_pct": float("nan"),
                "buffer_distance_impacts": {},
                "buffer_severity": None,
                "buffer_feature_types": [],
            }
            continue

        total_area = geom.area
        distance_impacts: Dict[float, float] = {}
        feature_types: set[str] = set()

        for distance_ft, union_geom in distance_groups.items():
            if union_geom.is_empty:
                distance_impacts[distance_ft] = 0.0
                continue
            intersection = geom.intersection(union_geom)
            if intersection.is_empty or total_area == 0.0:
                distance_impacts[distance_ft] = 0.0
                continue
            distance_impacts[distance_ft] = float((intersection.area / total_area) * 100.0)

        overall_geom = geom.intersection(combined_union)
        overall_pct = float((overall_geom.area / total_area) * 100.0) if total_area else 0.0

        # Identify feature types intersected
        for _, buffer_row in buffer_polygons.iterrows():
            if geom.intersects(buffer_row.geometry):
                feature_type = buffer_row.get("feature_type")
                if feature_type:
                    feature_types.add(feature_type)

        max_pct = max(distance_impacts.values(), default=0.0)
        severity_label = "none"
        for label, threshold in severity_sequence:
            if max_pct >= threshold:
                severity_label = label
        records[idx] = {
            "buffer_impacted_pct": overall_pct,
            "buffer_distance_impacts": distance_impacts,
            "buffer_severity": severity_label,
            "buffer_feature_types": sorted(feature_types),
        }

    assessment = pd.DataFrame.from_dict(records, orient="index")
    assessment.index = parcels.index
    return parcels.join(assessment)
