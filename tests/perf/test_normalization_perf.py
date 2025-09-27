from __future__ import annotations

from time import perf_counter

import numpy as np
import pytest

from aker_core.scoring import robust_minmax


@pytest.mark.performance
def test_robust_minmax_large_array_performance(record_property):
    rng = np.random.default_rng(123)
    values = rng.normal(size=500_000)

    start = perf_counter()
    result = robust_minmax(values)
    elapsed = perf_counter() - start

    record_property("elapsed_seconds", elapsed)
    record_property("array_size", result.size)

    assert np.isfinite(result).all()
    # Guard against pathological slowdowns; generous upper bound.
    assert elapsed < 1.0
