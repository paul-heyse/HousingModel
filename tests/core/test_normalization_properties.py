from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

_SCORING_SPEC = importlib.util.spec_from_file_location(
    "aker_core_scoring",
    Path(__file__).resolve().parents[2] / "src" / "aker_core" / "scoring.py",
)
assert _SCORING_SPEC and _SCORING_SPEC.loader
_SCORING_MODULE = importlib.util.module_from_spec(_SCORING_SPEC)
_SCORING_SPEC.loader.exec_module(_SCORING_MODULE)

RobustNormalizationError = _SCORING_MODULE.RobustNormalizationError
compute_winsor_bounds = _SCORING_MODULE.compute_winsor_bounds
robust_minmax = _SCORING_MODULE.robust_minmax

FINITE_FLOATS = st.floats(
    min_value=-1e9,
    max_value=1e9,
    allow_nan=False,
    allow_infinity=False,
    width=64,
)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=1, max_value=128),
        elements=FINITE_FLOATS | st.just(np.nan),
    )
)
def test_output_bounds(values: np.ndarray) -> None:
    if not np.isfinite(values).any():
        with pytest.raises(RobustNormalizationError):
            robust_minmax(values)
        return

    result = robust_minmax(values)
    finite_mask = np.isfinite(result)
    assert np.all(result[finite_mask] >= 0.0)
    assert np.all(result[finite_mask] <= 100.0)
    nan_mask = ~np.isfinite(values)
    if nan_mask.any():
        assert np.isnan(result[nan_mask]).all()


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=128),
        elements=FINITE_FLOATS,
    )
)
def test_monotonicity(values: np.ndarray) -> None:
    if not np.isfinite(values).any():
        with pytest.raises(RobustNormalizationError):
            robust_minmax(values)
        return

    sorted_values = np.sort(values.astype(float))
    result = robust_minmax(sorted_values)
    finite = result[np.isfinite(result)]
    assert np.all(np.diff(finite) >= -1e-9)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=128),
        elements=FINITE_FLOATS,
    ),
    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_scaling_invariance(values: np.ndarray, factor: float) -> None:
    if not np.isfinite(values).any():
        with pytest.raises(RobustNormalizationError):
            robust_minmax(values)
        return

    base = values.astype(float)
    scaled = base * factor
    base_norm = robust_minmax(base)
    scaled_norm = robust_minmax(scaled)
    assert np.allclose(base_norm, scaled_norm, equal_nan=True)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=1, max_value=64),
        elements=FINITE_FLOATS,
    )
)
def test_constant_array_collapses_to_midpoint(values: np.ndarray) -> None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        with pytest.raises(RobustNormalizationError):
            robust_minmax(values)
        return

    constant = np.full_like(values, finite[0] if finite.size else 0.0)
    result = robust_minmax(constant)
    assert np.allclose(result[np.isfinite(result)], 50.0)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=256),
        elements=FINITE_FLOATS,
    )
)
def test_compute_winsor_bounds_matches_percentiles(values: np.ndarray) -> None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        with pytest.raises(RobustNormalizationError):
            compute_winsor_bounds(values)
        return

    lower, upper = compute_winsor_bounds(values)
    expected = np.nanpercentile(finite, [5, 95])
    assert np.allclose([lower, upper], expected, atol=1e-9)
