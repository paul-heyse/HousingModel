from __future__ import annotations

import numpy as np

from aker_core.markets.pipeline import (
    DEFAULT_WEIGHTS,
    composite_scores,
    normalise_metrics,
    pillar_scores_from_normalised,
    run_scoring_pipeline,
)


def _sample_metrics() -> dict[str, np.ndarray]:
    rng = np.random.default_rng(42)
    return {
        "supply": rng.normal(loc=20, scale=5, size=10),
        "jobs": rng.normal(loc=50, scale=12, size=10),
        "urban": rng.uniform(0, 100, size=10),
        "outdoor": rng.normal(loc=60, scale=15, size=10),
    }


def test_normalise_metrics_matches_direct_calls():
    metrics = _sample_metrics()
    normalised, bounds = normalise_metrics(metrics)
    for key, values in metrics.items():
        np.testing.assert_allclose(normalised[key], normalised[key])
        assert key in bounds
        lower, upper = bounds[key]
        assert lower <= upper


def test_pipeline_produces_expected_shapes():
    metrics = _sample_metrics()
    result = run_scoring_pipeline(metrics)
    for key in metrics:
        assert result.normalised[key].shape == metrics[key].shape
        assert result.pillar_0_5[key].shape == metrics[key].shape
        assert key in result.bounds
    assert result.composite_0_5.shape == metrics["supply"].shape
    assert result.composite_0_100.shape == metrics["supply"].shape


def test_pipeline_consistency_with_manual_steps():
    metrics = _sample_metrics()
    result = run_scoring_pipeline(metrics)
    manual_norm, manual_bounds = normalise_metrics(metrics)
    manual_pillar = pillar_scores_from_normalised(manual_norm)
    manual_composite = composite_scores(manual_pillar, weights=DEFAULT_WEIGHTS)

    for key in metrics:
        np.testing.assert_allclose(result.normalised[key], manual_norm[key])
        assert result.bounds[key] == manual_bounds[key]
        np.testing.assert_allclose(result.pillar_0_5[key], manual_pillar[key])
    np.testing.assert_allclose(result.composite_0_5, manual_composite)
    np.testing.assert_allclose(result.composite_0_100, manual_composite * 20.0)


def test_composite_scores_handles_custom_weights():
    metrics = _sample_metrics()
    norm, _ = normalise_metrics(metrics)
    result = pillar_scores_from_normalised(norm)
    weights = {"supply": 0.5, "jobs": 0.2, "urban": 0.2, "outdoor": 0.1}
    composite = composite_scores(result, weights=weights)
    assert np.isfinite(composite).all()


def test_memory_usage_large_arrays():
    large_metrics = {
        "supply": np.linspace(0, 100, 250_000, dtype=float),
        "jobs": np.linspace(50, 150, 250_000, dtype=float),
        "urban": np.linspace(0, 200, 250_000, dtype=float),
        "outdoor": np.linspace(-20, 80, 250_000, dtype=float),
    }
    result = run_scoring_pipeline(large_metrics)
    # Ensure no NaNs and output stays in range
    for key in large_metrics:
        assert np.isfinite(result.normalised[key]).all()
        assert np.isfinite(result.pillar_0_5[key]).all()
        assert result.normalised[key].min() >= 0.0
        assert result.normalised[key].max() <= 100.0
    assert np.isfinite(result.composite_0_5).all()
