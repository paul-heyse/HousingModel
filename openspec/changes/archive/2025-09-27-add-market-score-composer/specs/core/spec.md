## MODIFIED Requirements
### Requirement: Market Score Composer
The system MUST provide a deterministic market score composer that combines pillar scores using documented weights and persists both 0–5 and 0–100 variants.

#### Scenario: Standard Weight Composition
- **WHEN** `markets.score(msa_id|msa_geo, as_of)` is executed with available pillar scores
- **THEN** the composer SHALL apply the standard weighting: 0.3×Supply + 0.3×Jobs + 0.2×Urban + 0.2×Outdoors
- **AND** yield both 0–5 and 0–100 composite scores persisted to `pillar_scores`
- **AND** missing pillars SHALL trigger validation errors rather than silent defaults

#### Scenario: Flexible Input Types
- **WHEN** calling the composer with different input types
- **THEN** it SHALL accept both MSA identifiers (strings) and geometries (Point/Polygon)
- **AND** resolve MSA boundaries for geographic inputs
- **AND** provide consistent scoring regardless of input type

#### Scenario: Deterministic Output
- **WHEN** the composer runs with identical pillar inputs
- **THEN** the resulting composite scores SHALL be deterministic and reproducible
- **AND** enable golden regression tests with fixed inputs
- **AND** support exact comparison of results across environments

#### Scenario: Configurable Weight Overrides
- **WHEN** pillar weights are overridden for scenario analysis
- **THEN** the composer SHALL accept custom weight dictionaries
- **AND** normalise weights to ensure they sum to 1.0
- **AND** track override metadata in persistence and lineage

#### Scenario: Pillar Weight Swap Testing
- **WHEN** testing pillar weight sensitivity
- **THEN** swapping weights (e.g., Supply vs Jobs) SHALL produce predictable score changes
- **AND** maintain mathematical consistency in weight application
- **AND** support regression tests for weight sensitivity analysis

#### Scenario: Persistence and Audit Trail
- **WHEN** composite scores are written to `pillar_scores`
- **THEN** the record SHALL include both 0–5 and 0–100 composite scores
- **AND** pillar breakdown scores for transparency
- **AND** weight scheme metadata and run identifier for auditability
- **AND** link to the `runs` table for complete lineage tracking

#### Scenario: Error Handling and Validation
- **WHEN** insufficient pillar data is available
- **THEN** the composer SHALL raise descriptive validation errors
- **AND** indicate which pillars are missing
- **AND** suggest potential data sources for missing pillars

#### Scenario: Performance and Scalability
- **WHEN** computing scores for multiple MSAs
- **THEN** the composer SHALL handle batch processing efficiently
- **AND** cache intermediate calculations where appropriate
- **AND** provide progress tracking for large-scale operations
