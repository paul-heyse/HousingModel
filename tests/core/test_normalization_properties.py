from __future__ import annotations

import numpy as np
from hypothesis import assume, given, settings, strategies as st
from hypothesis.extra.numpy import arrays

from aker_core.scoring import robust_minmax

FINITE_FLOATS = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
    width=64,
)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=128),
        elements=FINITE_FLOATS,
    )
)
def test_bounds_property(values: np.ndarray) -> None:
    assume(np.isfinite(values).any())
    scaled = robust_minmax(values)
    finite_mask = np.isfinite(scaled)
    assert np.all(scaled[finite_mask] >= 0.0)
    assert np.all(scaled[finite_mask] <= 100.0)


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=64),
        elements=FINITE_FLOATS,
    ),
    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_scaling_invariance(values: np.ndarray, factor: float) -> None:
    assume(np.isfinite(values).any())
    base = values.astype(float)
    scaled = base * factor
    assert np.allclose(robust_minmax(base), robust_minmax(scaled))


@settings(max_examples=200, deadline=None)
@given(
    arrays(
        dtype=np.float64,
        shape=st.integers(min_value=3, max_value=128),
        elements=FINITE_FLOATS,
    )
)
def test_monotonicity(values: np.ndarray) -> None:
    arr = np.sort(values.astype(float))
    assume(np.isfinite(arr).any())
    result = robust_minmax(arr)
    finite = result[np.isfinite(result)]
    assert np.all(np.diff(finite) >= -1e-9)
