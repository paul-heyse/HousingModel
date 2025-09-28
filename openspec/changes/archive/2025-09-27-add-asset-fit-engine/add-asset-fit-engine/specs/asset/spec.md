## ADDED Requirements

### Requirement: Asset Policy Guardrails & Fit Engine
The system SHALL evaluate an asset against policy guardrails and produce an `AssetFitResult` with a 0–100 fit score and explanatory flags.

#### Scenario: Product type eligibility
- **WHEN** an asset's product type is provided
- **THEN** the system SHALL validate it against allowed types for the specified context and emit a flag if disallowed

#### Scenario: Vintage band compliance
- **WHEN** an asset's year built is mapped to a vintage band
- **THEN** guardrails for that band (e.g., code, system standards) SHALL be checked and flags emitted on mismatch

#### Scenario: Unit mix and size checks
- **WHEN** unit mix and min/max size thresholds are provided
- **THEN** the system SHALL verify mix distribution and size bounds and emit flags for out‑of‑policy units

#### Scenario: Ceiling height minimums
- **WHEN** average and minimum ceiling heights are provided
- **THEN** the system SHALL compare to policy thresholds and emit flags for sub‑threshold values

#### Scenario: In‑unit washer/dryer policy
- **WHEN** in‑unit W/D presence is evaluated by product type and market segment
- **THEN** the system SHALL emit a flag when W/D requirements are unmet

#### Scenario: Parking ratios by context
- **WHEN** parking ratio and market context (e.g., transit‑rich, urban core) are provided
- **THEN** the system SHALL validate against context‑specific ratios and emit flags on shortfall/excess

#### Scenario: Fit scoring and weighting
- **WHEN** individual guardrail checks are evaluated
- **THEN** the system SHALL compute a 0–100 fit score using a transparent weighting scheme and ensure determinism for fixed inputs

#### Scenario: Result persistence and lineage
- **WHEN** a fit evaluation completes
- **THEN** results SHALL be persisted in `asset_fit` with inputs, ruleset/version, timestamp, and any overrides recorded

#### Scenario: Wizard examples as acceptance tests
- **WHEN** running the provided wizard examples
- **THEN** expected flags SHALL be produced and the arithmetic for the fit score SHALL be verified


