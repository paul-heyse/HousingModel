"""Scoring utilities for transforming raw indicators into standardized scores.

The primary entry point is :func:`robust_minmax`, a winsorised robust
min–max normaliser that maps arbitrary numeric inputs to the ``0–100`` scoring
range used across market pillars. The transformation can be expressed as::

    \\hat{x}_i = clip(x_i, q_{low}, q_{high})
    s_i = 100 * (\\hat{x}_i - q_{low}) / (q_{high} - q_{low})

where ``q_{low}`` and ``q_{high}`` are lower/upper quantiles estimated via
``np.nanpercentile`` after excluding non-finite observations. When the robust
range collapses (i.e. ``q_{low} == q_{high}``), the function returns the
midpoint score ``50`` while preserving ``NaN`` positions.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


class RobustNormalizationError(ValueError):
    """Raised when robust normalisation cannot be performed."""


def _as_float_array(values: Iterable[float]) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise RobustNormalizationError("Input must be array-like and numeric") from exc

    if array.ndim != 1:
        array = np.ravel(array)
    return array


def robust_minmax(
    values: Iterable[float],
    *,
    p_low: float = 0.05,
    p_high: float = 0.95,
) -> np.ndarray:
    """Winsorised robust min–max normalisation.

    Parameters
    ----------
    values
        Iterable of numeric values to normalise.
    p_low, p_high
        Lower and upper percentile bounds (expressed as fractions) used for winsorisation.

    Returns
    -------
    numpy.ndarray
        Array of floats in the closed interval ``[0.0, 100.0]``.

    Notes
    -----
    The transformation consists of three steps:

    1. Compute robust lower/upper bounds via ``np.nanpercentile`` using the
       supplied percentile parameters.
    2. Winsorise the input by clipping values to the computed bounds, ensuring
       extreme outliers do not dominate the scaling.
    3. Apply min–max normalisation to map the winsorised values onto ``[0, 100]``.

    The transformation is monotonic and scaling invariant provided the same
    percentile configuration is used, and always returns values within
    ``[0, 100]``. Constant inputs collapse to the centre point ``50``.
    """

    array = _as_float_array(values)
    finite_mask = np.isfinite(array)
    finite_values = array[finite_mask]

    if finite_values.size > 0:
        spread = float(np.nanmax(finite_values) - np.nanmin(finite_values))
        max_abs = float(np.nanmax(np.abs(finite_values))) if finite_values.size else 0.0
        tolerance = max(1e-12, max_abs * 1e-12)
        if spread <= tolerance:
            midpoint = np.full(array.shape, 50.0)
            return np.where(finite_mask, midpoint, np.nan)

    lower, upper = compute_winsor_bounds(array, p_low=p_low, p_high=p_high)
    result = apply_winsor_bounds(array, lower=lower, upper=upper)
    return result


def compute_winsor_bounds(
    values: Iterable[float],
    *,
    p_low: float = 0.05,
    p_high: float = 0.95,
) -> tuple[float, float]:
    """Return the winsorisation bounds for ``values``.

    This helper performs the same validation as :func:`robust_minmax` but only returns
    the computed lower/upper quantiles. Call :func:`apply_winsor_bounds` to reuse the
    bounds across multiple normalisation passes (e.g., scenario analysis).
    """

    array = _as_float_array(values)
    if array.size == 0:
        raise RobustNormalizationError("Input array is empty")

    finite_mask = np.isfinite(array)
    if not finite_mask.any():
        raise RobustNormalizationError("Input array contains no finite values")

    if not (0.0 <= p_low < p_high <= 1.0):
        raise RobustNormalizationError("Percentiles must satisfy 0 <= p_low < p_high <= 1")

    finite_values = array[finite_mask]
    lower = np.nanpercentile(finite_values, p_low * 100.0)
    upper = np.nanpercentile(finite_values, p_high * 100.0)

    if not np.isfinite(lower) or not np.isfinite(upper):
        raise RobustNormalizationError("Percentile computation produced non-finite bounds")

    if upper < lower:
        lower, upper = upper, lower

    return float(lower), float(upper)


def apply_winsor_bounds(array: np.ndarray, *, lower: float, upper: float) -> np.ndarray:
    """Apply precomputed winsor bounds and return the 0–100 normalised scores."""

    finite_mask = np.isfinite(array)
    finite_values = array[finite_mask]

    if finite_values.size == 0:
        return np.full(array.shape, np.nan)

    spread = float(np.nanmax(finite_values) - np.nanmin(finite_values))
    if spread <= 1e-12:
        midpoint = np.full(array.shape, 50.0)
        return np.where(finite_mask, midpoint, np.nan)

    if np.isclose(upper, lower):
        unique_values = np.unique(finite_values)
        if unique_values.size > 1:
            lower = float(unique_values.min())
            upper = float(unique_values.max())
        else:
            midpoint = np.full(array.shape, 50.0)
            return np.where(finite_mask, midpoint, np.nan)

    scale = max(abs(lower), abs(upper), 1.0)
    clipped = np.clip(array / scale, lower / scale, upper / scale)
    normalised = (clipped - (lower / scale)) / ((upper / scale) - (lower / scale))
    normalised *= 100.0
    normalised = np.where(finite_mask, normalised, np.nan)
    normalised = np.clip(normalised, 0.0, 100.0)
    # Clamp tiny floating errors so scaled invariance holds under percentile collapse
    normalised = np.where(np.isclose(normalised, 0.0, atol=1e-6), 0.0, normalised)
    normalised = np.where(np.isclose(normalised, 100.0, atol=1e-6), 100.0, normalised)
    return normalised.astype(float, copy=False)


__all__ = [
    "robust_minmax",
    "RobustNormalizationError",
    "compute_winsor_bounds",
    "apply_winsor_bounds",
]
