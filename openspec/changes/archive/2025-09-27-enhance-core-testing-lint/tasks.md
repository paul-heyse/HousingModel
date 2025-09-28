## 1. Restore Property-Based Normalization Coverage
- [x] 1.1 Reintroduce Hypothesis-driven tests for `robust_minmax`, covering bounds, monotonicity, scaling invariance, and NaN handling.
- [x] 1.2 Ensure the tests run deterministically in CI (profile settings, Hypothesis seed) to avoid flakes.

## 2. Lint Debt Remediation
- [x] 2.1 Organise imports and remove unused symbols across demo/legacy scripts surfaced by `ruff` (migrations, demo_complete_*.py, simple test harnesses).
- [x] 2.2 Move long-term demos/examples under a dedicated namespace or update the lint configuration to exclude them explicitly, documenting the rationale.

## 3. Quality Gates
- [x] 3.1 Run `ruff check .` and `pytest -q` to confirm a clean baseline after the cleanup.
