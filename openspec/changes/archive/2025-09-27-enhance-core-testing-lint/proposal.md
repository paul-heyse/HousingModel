## Why
Recent review flagged lingering technical debt outside the geospatial fixes: the property-based suite for `robust_minmax` was replaced by deterministic RNG loops (weakening regression coverage) and dozens of demo/legacy modules still fail `ruff` due to unsorted or unused imports. Those gaps keep showing up in every lint run and obscure real issues.

## What Changes
- Reinstate Hypothesis-backed normalization property tests to enforce bounds, monotonicity, and scaling invariance with the modern validation stack.
- Clean or quarantine demo/legacy scripts so project linting can run green again (organise imports, drop unused symbols, or move them under an examples namespace with a targeted lint exclude).
- Update lint configuration/documentation to keep non-production assets from regressing and ensure the default `ruff check` surface only actionable violations.

## Impact
- Affected specs: core
- Affected code: `tests/core/test_normalization_properties.py`, demo scripts under repo root, lint configuration.
