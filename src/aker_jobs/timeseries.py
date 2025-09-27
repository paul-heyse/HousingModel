"""Time-series utilities for jobs analysis."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def _infer_years(series: pd.Series) -> float:
    index = series.index
    if isinstance(index, pd.DatetimeIndex):
        years = (index[-1] - index[0]).days / 365.25
        return max(years, 1.0)
    if isinstance(index, pd.PeriodIndex):
        years = index[-1].year - index[0].year or 1
        return float(years)
    length = len(series) - 1
    return float(max(length, 1))


def cagr(series: Iterable[float] | pd.Series, *, years: float | None = None) -> float:
    """Compute compound annual growth rate for a time series.

    Zero or negative values are nudged by a small epsilon to maintain numerical
    stability while preserving directionality.
    """

    data = pd.Series(series).dropna()
    if data.empty:
        raise ValueError("Series must contain at least one value")

    if years is None:
        years = _infer_years(data)
    if years <= 0:
        raise ValueError("Years must be positive")

    start = float(data.iloc[0])
    end = float(data.iloc[-1])
    epsilon = 1e-9

    if abs(start) < epsilon and abs(end) < epsilon:
        return 0.0

    start_adj = start if abs(start) > epsilon else epsilon
    end_adj = end if abs(end) > epsilon else epsilon

    growth = (end_adj / start_adj) ** (1.0 / years) - 1.0
    if start < 0 < end:
        growth = np.sign(end - start) * abs(growth)
    return float(growth)
