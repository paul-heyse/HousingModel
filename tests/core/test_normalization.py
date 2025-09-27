from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from aker_core.scoring import RobustNormalizationError, robust_minmax


class TestRobustMinMax:
    def test_bounds_guarantee(self) -> None:
        values = [1, 5, 10, 15, 100]
        result = robust_minmax(values)
        assert np.all(result >= 0.0)
        assert np.all(result <= 100.0)

    def test_constant_returns_midpoint(self) -> None:
        result = robust_minmax([5, 5, 5])
        assert np.allclose(result, 50.0)

    def test_single_value(self) -> None:
        result = robust_minmax([42])
        assert result.shape == (1,)
        assert result[0] == pytest.approx(50.0)

    def test_empty_array_raises(self) -> None:
        with pytest.raises(RobustNormalizationError):
            robust_minmax([])

    def test_all_nan_raises(self) -> None:
        with pytest.raises(RobustNormalizationError):
            robust_minmax([np.nan, np.nan])

    def test_percentile_validation(self) -> None:
        with pytest.raises(RobustNormalizationError):
            robust_minmax([1, 2, 3], p_low=0.5, p_high=0.1)

    def test_monotonicity(self) -> None:
        base = np.array([1, 2, 3, 4, 5], dtype=float)
        scaled = base + 1
        norm_base = robust_minmax(base)
        norm_scaled = robust_minmax(scaled)
        assert np.all(norm_base <= norm_scaled + 1e-9)

    def test_scaling_invariance(self) -> None:
        base = np.array([10, 20, 30, 40, 50], dtype=float)
        scaled = base * 3.7
        assert np.allclose(robust_minmax(base), robust_minmax(scaled))

    def test_numerical_stability_small_range(self) -> None:
        tiny = np.array([1.000001, 1.000002, 1.000003])
        result = robust_minmax(tiny)
        assert np.all(np.isfinite(result))

    def test_winsorisation_effect(self) -> None:
        data = np.array([1, 2, 3, 4, 1000, 2000], dtype=float)
        default = robust_minmax(data)
        tighter = robust_minmax(data, p_low=0.2, p_high=0.8)
        assert tighter[-1] <= default[-1]
        assert default[-1] > default[-2]  # ensure extreme was influencing default case

    def test_performance_vectorised(self) -> None:
        rng = np.random.default_rng(42)
        arr = rng.normal(size=200_000)
        result = robust_minmax(arr)
        assert result.size == arr.size
        assert np.isfinite(result).all()

    def test_nan_preservation(self) -> None:
        arr = np.array([1.0, np.nan, 5.0])
        result = robust_minmax(arr)
        assert math.isnan(result[1])

    def test_integration_with_array_like(self) -> None:
        result = robust_minmax((1, 2, 3, 4))
        assert np.all(np.diff(result) >= 0)


class TestGoldenMaster:
    def test_snapshot_matches_expected_values(self) -> None:
        snapshot_path = Path(__file__).parent.parent / "data" / "robust_minmax_snapshot.json"
        payload = json.loads(snapshot_path.read_text())
        values = np.array(payload["input"], dtype=float)

        default = robust_minmax(values)
        tight = robust_minmax(values, p_low=0.1, p_high=0.9)

        np.testing.assert_allclose(default, payload["expected"]["default"], rtol=1e-9, atol=1e-9)
        np.testing.assert_allclose(tight, payload["expected"]["tight"], rtol=1e-9, atol=1e-9)
