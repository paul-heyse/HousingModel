"""Slope analysis utilities built on top of digital elevation models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping

import geopandas as gpd
import numpy as np
import pandas as pd

from .dem import DigitalElevationModel

DEFAULT_SEVERITY_THRESHOLDS: Mapping[str, tuple[float, float]] = {
    "flat": (0.0, 5.0),
    "moderate": (5.0, 15.0),
    "steep": (15.0, 25.0),
    "extreme": (25.0, float("inf")),
}

DEFAULT_DEVELOPMENT_THRESHOLDS: Mapping[str, float] = {
    "residential": 15.0,
    "mixed_use": 12.0,
    "commercial": 10.0,
}


@dataclass(frozen=True)
class SlopeStatistics:
    """Summary statistics for a single parcel."""

    mean_pct: float
    max_pct: float
    std_pct: float
    constrained_area_pct: float
    primary_severity: str | None
    severity_breakdown: Dict[str, float]
    development_constraints: Dict[str, float]
    confidence: float
    cell_count: int


class SlopeAnalysisError(RuntimeError):
    """Raised when slope analysis fails due to invalid inputs."""


def _normalise_thresholds(
    thresholds: Mapping[str, tuple[float, float]] | Iterable[tuple[str, tuple[float, float]]]
) -> Dict[str, tuple[float, float]]:
    if isinstance(thresholds, Mapping):
        items = thresholds.items()
    else:
        items = thresholds
    ordered = sorted(items, key=lambda item: item[1][0])
    normalised: Dict[str, tuple[float, float]] = {}
    for label, (low, high) in ordered:
        if high <= low:
            raise ValueError(f"Invalid threshold range for '{label}': {(low, high)}")
        normalised[label] = (float(low), float(high))
    return normalised


def slope_percent(
    parcels: gpd.GeoDataFrame,
    dem: DigitalElevationModel,
    *,
    slope_threshold_deg: float = 15.0,
    severity_thresholds: (
        Mapping[str, tuple[float, float]] | Iterable[tuple[str, tuple[float, float]]] | None
    ) = None,
    development_thresholds: Mapping[str, float] | None = None,
) -> gpd.GeoDataFrame:
    """Calculate slope statistics for each parcel using the provided DEM.

    Parameters
    ----------
    parcels:
        GeoDataFrame containing polygonal geometries to evaluate.
    dem:
        DigitalElevationModel instance with elevation samples covering the
        parcel footprints.
    slope_threshold_deg:
        Threshold in degrees used to classify constrained terrain.
    severity_thresholds:
        Optional mapping of severity label to (min_deg, max_deg) ranges.  When
        omitted a sensible default classification is used.
    development_thresholds:
        Optional mapping of development type to slope thresholds (degrees) used
        to compute constraint coverage per development scenario.

    Returns
    -------
    GeoDataFrame
        Original parcels with appended slope statistics columns.
    """

    if not isinstance(parcels, gpd.GeoDataFrame):
        raise TypeError("parcels must be a GeoDataFrame")
    if parcels.empty:
        raise ValueError("parcels GeoDataFrame is empty")
    if parcels.geometry.isna().any():
        raise SlopeAnalysisError("parcels contain missing geometries")

    severity_thresholds = _normalise_thresholds(severity_thresholds or DEFAULT_SEVERITY_THRESHOLDS)
    if development_thresholds is None:
        development_thresholds = dict(DEFAULT_DEVELOPMENT_THRESHOLDS)

    slope_pct_grid = dem.slope_percent_grid()
    slope_deg_grid = dem.slope_degrees_grid()

    records: MutableMapping[int, SlopeStatistics] = {}

    for idx, geometry in parcels.geometry.items():
        if geometry is None or geometry.is_empty:
            stats = SlopeStatistics(
                mean_pct=float("nan"),
                max_pct=float("nan"),
                std_pct=float("nan"),
                constrained_area_pct=float("nan"),
                primary_severity=None,
                severity_breakdown={label: float("nan") for label in severity_thresholds},
                development_constraints={key: float("nan") for key in development_thresholds},
                confidence=0.0,
                cell_count=0,
            )
            records[idx] = stats
            continue

        mask = dem.mask_geometry(geometry)
        if not mask.any():
            stats = SlopeStatistics(
                mean_pct=float("nan"),
                max_pct=float("nan"),
                std_pct=float("nan"),
                constrained_area_pct=float("nan"),
                primary_severity=None,
                severity_breakdown={label: float("nan") for label in severity_thresholds},
                development_constraints={key: float("nan") for key in development_thresholds},
                confidence=0.0,
                cell_count=0,
            )
            records[idx] = stats
            continue

        valid_mask = dem.valid_mask & mask
        total_cells = int(mask.sum())
        valid_cells = int(valid_mask.sum())

        if valid_cells == 0:
            stats = SlopeStatistics(
                mean_pct=float("nan"),
                max_pct=float("nan"),
                std_pct=float("nan"),
                constrained_area_pct=float("nan"),
                primary_severity=None,
                severity_breakdown={label: float("nan") for label in severity_thresholds},
                development_constraints={key: float("nan") for key in development_thresholds},
                confidence=0.0,
                cell_count=0,
            )
            records[idx] = stats
            continue

        slope_pct_values = slope_pct_grid[valid_mask]
        slope_deg_values = slope_deg_grid[valid_mask]

        mean_pct = float(np.nanmean(slope_pct_values))
        max_pct = float(np.nanmax(slope_pct_values))
        std_pct = float(np.nanstd(slope_pct_values))

        constrained_mask = slope_deg_values > slope_threshold_deg
        constrained_area_pct = float(constrained_mask.mean() * 100.0)

        severity_breakdown: Dict[str, float] = {}
        severity_primary_label: str | None = None
        severity_primary_value = -1.0
        for label, (low, high) in severity_thresholds.items():
            severity_mask = (slope_deg_values >= low) & (slope_deg_values < high)
            percentage = float(severity_mask.mean() * 100.0)
            severity_breakdown[label] = percentage
            if percentage > severity_primary_value:
                severity_primary_label = label
                severity_primary_value = percentage

        development_constraints_pct: Dict[str, float] = {}
        for scenario, threshold in development_thresholds.items():
            mask_threshold = slope_deg_values > threshold
            development_constraints_pct[scenario] = float(mask_threshold.mean() * 100.0)

        confidence = float(valid_cells / total_cells)

        stats = SlopeStatistics(
            mean_pct=mean_pct,
            max_pct=max_pct,
            std_pct=std_pct,
            constrained_area_pct=constrained_area_pct,
            primary_severity=severity_primary_label,
            severity_breakdown=severity_breakdown,
            development_constraints=development_constraints_pct,
            confidence=confidence,
            cell_count=valid_cells,
        )
        records[idx] = stats

    stats_frame = pd.DataFrame.from_dict(
        {
            idx: {
                "slope_mean_pct": stats.mean_pct,
                "slope_max_pct": stats.max_pct,
                "slope_std_pct": stats.std_pct,
                "slope_constrained_area_pct": stats.constrained_area_pct,
                "slope_primary_severity": stats.primary_severity,
                "slope_severity_breakdown": stats.severity_breakdown,
                "slope_development_constraints": stats.development_constraints,
                "slope_confidence": stats.confidence,
                "slope_cell_count": stats.cell_count,
            }
            for idx, stats in records.items()
        },
        orient="index",
    )

    return parcels.join(stats_frame)
