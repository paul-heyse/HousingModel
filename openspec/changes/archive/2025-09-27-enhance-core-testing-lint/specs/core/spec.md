## ADDED Requirements
### Requirement: Core Normalization Properties Are Property-Tested
The scoring utilities SHALL retain property-based tests (Hypothesis or equivalent) that exercise `robust_minmax` over a wide numeric domain, validating bounds, monotonicity, scaling invariance, and NaN propagation so future regressions surface automatically.

#### Scenario: Property Suite Guards Against Regression
- **WHEN** the normalization implementation changes
- **THEN** the Hypothesis suite SHALL run in CI and fail on deviations from the documented invariants (e.g., values escaping [0,100] or scaling invariance breaking)

### Requirement: Lint Surface Remains Actionable
Linting SHALL run clean by default, either because legacy/demo modules conform to style/import rules or are isolated from the production lint config with documented exclusions.

#### Scenario: `ruff check .` Passes Without Demo Noise
- **WHEN** contributors run `ruff check .`
- **THEN** the command SHALL complete without raising errors from demo scripts or migrations, ensuring lint failures indicate actionable regressions
