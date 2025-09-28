## ADDED Requirements
### Requirement: Risk Engine Hazard Multipliers
The system SHALL provide a risk engine that computes peril-specific severity indices and underwriting multipliers in range 0.90–1.10 for both markets and assets, exposing a Python surface that downstream underwriting and reporting workflows can consume.

#### Scenario: Compute Returns RiskEntry
- **GIVEN** a market or asset identifier and a supported peril (e.g., `"wildfire"`, `"hail"`, `"snow_load"`, `"water_stress"`, `"policy_risk"`)
- **WHEN** `risk.compute(subject, peril)` is called with the latest hazard datasets
- **THEN** the function SHALL return a `RiskEntry` dataclass containing `multiplier` (float), `severity_idx` (0–100), and `deductible` metadata appropriate for the peril
- **AND** the multiplier SHALL be clamped to the inclusive range `[0.90, 1.10]`

#### Scenario: Monotonic Severity To Multiplier Mapping
- **GIVEN** two inputs for the same peril where `severity_idx_a < severity_idx_b`
- **WHEN** `risk.compute` is executed for each input using the same configuration
- **THEN** the resulting multipliers SHALL satisfy `multiplier_a >= multiplier_b` for benefit perils (e.g., lower severity → higher multiplier) and vice versa for adverse perils, with calibration profiles documented and unit-tested

#### Scenario: Apply Risk To Underwriting
- **GIVEN** an underwriting payload with base assumptions (exit cap, contingencies, insurance deductibles)
- **WHEN** `RiskEngine.apply_to_underwrite(payload, risk_entries)` is invoked with one or more `RiskEntry` objects
- **THEN** the engine SHALL apply compounded multipliers, annotate the payload with peril-level adjustments, and record the applied risk profile identifier for auditability

#### Scenario: Persist Risk Profile
- **WHEN** `risk.compute` produces a `RiskEntry`
- **THEN** the system SHALL persist the result to the `risk_profile` table with fields: `subject_type`, `subject_id`, `peril`, `severity_idx`, `multiplier`, `deductible`, `data_vintage`, `run_id`, `calculation_method`
- **AND** subsequent requests in the same run MAY reuse the persisted value instead of recomputing

#### Scenario: Reporting Integration
- **GIVEN** an investment memo or IC packet export
- **WHEN** the report is generated for a market or asset with stored risk profile entries
- **THEN** the report SHALL include the peril table with severity indices, multipliers, deductible guidance, data vintage, and narrative flags sourced from the persisted `risk_profile`

#### Scenario: Testing And DoD
- **WHEN** unit tests execute for the risk engine module
- **THEN** each peril SHALL have dedicated bounds tests (multiplier stays within 0.90–1.10), monotonicity/property tests for severity mapping, and integration tests that round-trip `risk.compute` → `RiskEngine.apply_to_underwrite` → report serialization
- **AND** golden-master samples SHALL exist for at least one market and one asset to guard against regressions

#### Scenario: Configuration And Overrides
- **WHEN** operators provide calibration overrides (e.g., custom breakpoints per region)
- **THEN** the risk engine SHALL accept structured configuration, record the configuration version in `calculation_method`, and emit lineage entries for all hazard data sources used during computation
