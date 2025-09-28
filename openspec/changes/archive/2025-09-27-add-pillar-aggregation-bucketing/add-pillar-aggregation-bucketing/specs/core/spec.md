## ADDED Requirements

### Requirement: Pillar Score Aggregation Engine
The system SHALL provide a comprehensive `scoring.pillar_score()` function in `aker_core.scoring` that calculates weighted mean scores from normalized 0-100 pillar metrics using configurable weighting schemes with full mathematical validation.

#### Scenario: Standard Aker Four-Pillar Weighting
- **GIVEN** normalized metrics for Supply, Jobs, Urban, and Outdoors pillars (0-100 values)
- **WHEN** `scoring.pillar_score(metrics, weights)` is called with standard Aker weights (Supply: 0.3, Jobs: 0.3, Urban: 0.2, Outdoors: 0.2)
- **THEN** the function SHALL return the weighted mean: `0.3*Supply + 0.3*Jobs + 0.2*Urban + 0.2*Outdoors`
- **AND** the result SHALL be a float with precision appropriate for financial calculations
- **AND** the calculation SHALL be mathematically equivalent to: `sum(metric * weight for metric, weight in zip(metrics.values(), weights.values()))`

#### Scenario: Custom Weight Validation and Normalization
- **GIVEN** a weights dictionary with values that do not sum to 1.0
- **WHEN** `pillar_score()` is called with `normalize_weights=True`
- **THEN** the function SHALL automatically normalize weights to sum to 1.0
- **AND** issue a warning about weight normalization
- **AND** proceed with the normalized calculation

#### Scenario: Strict Weight Validation
- **GIVEN** a weights dictionary with values that do not sum to 1.0
- **WHEN** `pillar_score()` is called with `normalize_weights=False`
- **THEN** the function SHALL raise ValueError with message: "Weights must sum to 1.0, got {actual_sum}"
- **AND** the error SHALL specify the actual sum of weights for debugging

#### Scenario: Missing Metric Detection
- **GIVEN** a metrics dictionary missing required pillar keys
- **WHEN** `pillar_score()` is called
- **THEN** the function SHALL raise KeyError with message: "Missing required metric: {missing_key}"
- **AND** the error SHALL specify exactly which metric key is missing
- **AND** the function SHALL not proceed with partial calculations

#### Scenario: Input Type and Range Validation
- **GIVEN** invalid input types or out-of-range values
- **WHEN** `pillar_score()` is called
- **THEN** the function SHALL validate that metrics is a dictionary with string keys
- **AND** all metric values SHALL be numeric (int/float) in range [0, 100]
- **AND** all weight values SHALL be numeric (int/float) in range [0, 1]
- **AND** raise appropriate TypeError or ValueError with descriptive messages

#### Scenario: Mathematical Properties
- **GIVEN** two sets of metrics where all values in set A are ≤ corresponding values in set B
- **WHEN** `pillar_score()` is called on both sets with identical weights
- **THEN** the result for set A SHALL be ≤ the result for set B (monotonicity)
- **AND** this property SHALL hold for all valid weight combinations

### Requirement: Advanced 0-5 Bucket Mapping System
The system SHALL provide a sophisticated `scoring.to_five_bucket()` function in `aker_core.scoring` that maps 0-100 pillar scores to 0-5 scale using configurable quantile-based bucketing with statistical validation.

#### Scenario: Standard Quantile-Based Bucketing
- **GIVEN** a 0-100 pillar score value
- **WHEN** `scoring.to_five_bucket(value)` is called with default parameters
- **THEN** the function SHALL return an integer 0-5 based on quantile mapping
- **AND** the mapping SHALL use [20, 40, 60, 80] as the bucket boundaries
- **AND** values SHALL be mapped as: 0-20→0, 20-40→1, 40-60→2, 60-80→3, 80-100→4

#### Scenario: Configurable Bucket Boundaries
- **GIVEN** custom bucket boundaries specified as a parameter
- **WHEN** `to_five_bucket(value, boundaries=[15, 35, 55, 75, 95])` is called
- **THEN** the function SHALL use the custom boundaries for mapping
- **AND** validate that boundaries are sorted and within [0, 100]
- **AND** boundaries SHALL define 5 buckets (requiring 4 boundary values)

#### Scenario: Boundary Value Edge Cases
- **GIVEN** boundary values (0, 20, 40, 60, 80, 100) or custom equivalents
- **WHEN** `to_five_bucket()` is called
- **THEN** the function SHALL correctly map boundary values to appropriate buckets
- **AND** value exactly equal to a boundary SHALL map to the higher bucket
- **AND** value 0 SHALL always map to bucket 0
- **AND** value 100 SHALL always map to bucket 4 (highest)

#### Scenario: Input Validation and Error Handling
- **GIVEN** invalid input values (negative, >100, non-numeric, NaN, infinity)
- **WHEN** `to_five_bucket()` is called
- **THEN** the function SHALL raise ValueError for out-of-range values with message: "Value must be in range [0, 100], got {value}"
- **AND** raise TypeError for non-numeric inputs with message: "Input must be numeric, got {type}"
- **AND** handle NaN and infinity values appropriately with clear error messages

#### Scenario: Statistical Consistency
- **GIVEN** the same set of 0-100 values processed multiple times
- **WHEN** `to_five_bucket()` is called with identical parameters
- **THEN** the function SHALL produce identical results (deterministic)
- **AND** the mapping SHALL be consistent across different execution environments

### Requirement: Comprehensive Database Persistence Layer
The system SHALL persist pillar scores in a robust `pillar_scores` table with complete run tracking, risk multiplier integration, and comprehensive metadata for auditability and performance.

#### Scenario: Complete Score Persistence With Run Context
- **GIVEN** calculated pillar scores for a market analysis run
- **WHEN** scores are persisted using the database layer
- **THEN** each record SHALL include: `run_id`, `msa_id`, `supply_score_0_5`, `jobs_score_0_5`, `urban_score_0_5`, `outdoors_score_0_5`, `weighted_score_0_5`, `risk_multiplier`, `calculated_at`, `data_vintage`
- **AND** the `run_id` SHALL link to the active `RunContext` with full traceability
- **AND** the `risk_multiplier` (0.90-1.10) SHALL be applied to the weighted score for final adjusted results

#### Scenario: Risk Multiplier Integration and Application
- **GIVEN** a market with calculated pillar scores and risk assessment
- **WHEN** scores are persisted
- **THEN** the `risk_multiplier` (0.90-1.10) SHALL be stored alongside pillar scores
- **AND** the system SHALL calculate `final_adjusted_score = weighted_score_0_5 * risk_multiplier`
- **AND** the risk multiplier SHALL be applied to exit cap rate calculations in underwriting workflows
- **AND** the multiplier SHALL reflect market-specific perils (wildfire, hail, water stress, etc.)

#### Scenario: Data Integrity and Constraint Enforcement
- **GIVEN** pillar score records being inserted
- **WHEN** database constraints are enforced
- **THEN** all pillar scores SHALL be valid integers in range 0-5 inclusive
- **AND** risk multipliers SHALL be valid floats in range 0.90-1.10 inclusive
- **AND** `run_id` SHALL reference a valid run record with foreign key constraint
- **AND** `msa_id` SHALL reference a valid MSA record
- **AND** all timestamp fields SHALL be automatically populated

#### Scenario: Advanced Query and Retrieval Capabilities
- **GIVEN** stored pillar scores in the database
- **WHEN** querying by various criteria
- **THEN** the system SHALL support efficient queries by `msa_id`, `run_id`, date ranges, score ranges
- **AND** results SHALL include all pillar components, risk multiplier, and metadata
- **AND** results SHALL be ordered by most recent run first (default) or by specified criteria
- **AND** the system SHALL support pagination for large result sets

#### Scenario: Performance Optimization
- **GIVEN** the `pillar_scores` table with potentially millions of records
- **WHEN** executing common query patterns
- **THEN** the system SHALL use composite indexes on `(msa_id, calculated_at)`, `(run_id)`, and `(weighted_score_0_5)`
- **AND** query performance SHALL be optimized for dashboard loading (sub-second response times)
- **AND** the system SHALL support batch insert operations for bulk scoring runs

#### Scenario: Audit Trail and Data Lineage
- **GIVEN** pillar scores stored in the database
- **WHEN** tracking data provenance and audit requirements
- **THEN** each record SHALL include `data_vintage` indicating the source data timestamp
- **AND** `calculation_method` SHALL specify the exact algorithm version used
- **AND** `run_id` SHALL provide complete traceability to input data and configuration
- **AND** the system SHALL support querying historical scores for trend analysis
