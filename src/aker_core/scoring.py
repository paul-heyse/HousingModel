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

    if np.isclose(upper, lower):
        result = np.full(array.shape, 50.0)
        return np.where(np.isfinite(array), result, np.nan)

    clipped = np.clip(array, lower, upper)
    normalised = (clipped - lower) / (upper - lower)
    normalised *= 100.0

    normalised = np.where(np.isfinite(array), normalised, np.nan)
    # Guard numerical drift
    normalised = np.clip(normalised, 0.0, 100.0)
    return normalised.astype(float, copy=False)


__all__ = ["robust_minmax", "RobustNormalizationError"]
