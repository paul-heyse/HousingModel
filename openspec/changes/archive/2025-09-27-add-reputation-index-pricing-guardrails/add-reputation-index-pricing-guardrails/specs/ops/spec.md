## ADDED Requirements

### Requirement: Reputation Index Calculation
The system SHALL compute a 0–100 Reputation Index from review signals and NPS.

#### Scenario: Deterministic index from inputs
- **WHEN** reviews and NPS are provided
- **THEN** the function `ops.reputation_index(reviews, nps)` SHALL return a float in [0, 100] deterministically for fixed inputs

#### Scenario: Predictable synthetic shifts
- **WHEN** synthetic inputs increase positive reviews by 10% keeping NPS constant
- **THEN** the index SHALL increase by a predictable delta within configured weight tolerances

### Requirement: Pricing and Concession Guardrails
The system SHALL produce pricing/concession guardrails derived from the Reputation Index.

#### Scenario: Pricing rules output
- **WHEN** `ops.pricing_rules(index)` is called with an index value
- **THEN** it SHALL return structured guardrails (e.g., max discount %, concession days) consistent with configured thresholds

#### Scenario: Bounds and monotonicity
- **WHEN** index increases
- **THEN** allowed concessions SHALL not increase and allowed price uplift bounds SHALL not decrease

### Requirement: Persistence and Lineage
The system SHALL persist results to `ops_model` with input snapshots and versioning.

#### Scenario: Record storage
- **WHEN** an index is computed
- **THEN** a row SHALL be inserted/updated with index, rules, inputs hash, version, timestamp

