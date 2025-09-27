"""Market scoring pipeline helpers built on top of robust normalisation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping

import numpy as np

from aker_core.scoring import robust_minmax

DEFAULT_WEIGHTS: Dict[str, float] = {
    "supply": 0.30,
    "jobs": 0.30,
    "urban": 0.20,
    "outdoor": 0.20,
}


@dataclass(frozen=True)
class NormalisationResult:
    """Container for normalised pillar metrics and derived scores."""

    normalised: Dict[str, np.ndarray]
    pillar_0_5: Dict[str, np.ndarray]
    composite_0_5: np.ndarray
    composite_0_100: np.ndarray


def normalise_metrics(
    metrics: Mapping[str, Iterable[float]],
    *,
    p_low: float = 0.05,
    p_high: float = 0.95,
) -> Dict[str, np.ndarray]:
    """Apply :func:`robust_minmax` to each metric array.

    Parameters
    ----------
    metrics
        Mapping of metric name → array-like values (one value per market).
    p_low, p_high
        Percentile parameters forwarded to :func:`robust_minmax`.

    Returns
    -------
    dict
        Mapping with the same keys where each value is a ``float64`` array.
    """

    normalised: Dict[str, np.ndarray] = {}
    for name, values in metrics.items():
        array = robust_minmax(values, p_low=p_low, p_high=p_high)
        normalised[name] = array.astype(float, copy=False)
    return normalised


def pillar_scores_from_normalised(
    normalised: Mapping[str, np.ndarray],
) -> Dict[str, np.ndarray]:
    """Convert normalised ``0–100`` scores into pillar ``0–5`` bands."""

    pillar_scores: Dict[str, np.ndarray] = {}
    for name, values in normalised.items():
        pillar_scores[name] = values / 20.0
    return pillar_scores


def composite_scores(
    pillar_scores: Mapping[str, np.ndarray],
    *,
    weights: Mapping[str, float] | None = None,
) -> np.ndarray:
    """Compute weighted composite scores from pillar ``0–5`` data."""

    weights = dict(weights or DEFAULT_WEIGHTS)
    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0):
        weights = {k: v / total_weight for k, v in weights.items()}

    # Determine output length from first pillar
    length = len(next(iter(pillar_scores.values())))
    composite = np.zeros(length, dtype=float)
    for pillar, weight in weights.items():
        if pillar not in pillar_scores:
            raise KeyError(f"Missing pillar '{pillar}' in pillar_scores mapping")
        composite += pillar_scores[pillar] * weight
    return composite


def run_scoring_pipeline(
    metrics: Mapping[str, Iterable[float]],
    *,
    p_low: float = 0.05,
    p_high: float = 0.95,
    weights: Mapping[str, float] | None = None,
) -> NormalisationResult:
    """Execute normalisation → pillar scaling → composite score pipeline."""

    normalised = normalise_metrics(metrics, p_low=p_low, p_high=p_high)
    pillar_0_5 = pillar_scores_from_normalised(normalised)
    composite_0_5 = composite_scores(pillar_0_5, weights=weights)
    composite_0_100 = composite_0_5 * 20.0
    return NormalisationResult(
        normalised=normalised,
        pillar_0_5=pillar_0_5,
        composite_0_5=composite_0_5,
        composite_0_100=composite_0_100,
    )


__all__ = [
    "NormalisationResult",
    "normalise_metrics",
    "pillar_scores_from_normalised",
    "composite_scores",
    "run_scoring_pipeline",
]
