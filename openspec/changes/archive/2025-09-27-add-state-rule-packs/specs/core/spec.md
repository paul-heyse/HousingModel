## ADDED Requirements
### Requirement: State Rule Packs Engine
The system SHALL provide a state-specific rule pack engine that applies location-based defaults, perils, winterization cost adders, and tax cadences with particular emphasis on CO/UT/ID operational characteristics.

#### Scenario: Colorado State Pack Application
- **GIVEN** a Colorado market context with aerospace/tech/health industry anchors
- **WHEN** `state_packs.apply("CO", context)` is called
- **THEN** the system SHALL apply CO-specific defaults including hail/wildfire insurance patterns
- **AND** entitlement variance adjustments SHALL be applied to guardrails
- **AND** winterization cost adders SHALL account for hail exposure and severe weather patterns

#### Scenario: Utah State Pack Application
- **GIVEN** a Utah market context with topography-driven supply constraints
- **WHEN** `state_packs.apply("UT", context)` is called
- **THEN** the system SHALL apply UT-specific topography friction adjustments
- **AND** water rights and winter timing considerations SHALL modify tax cadence
- **AND** higher-ed and tech anchor effects SHALL adjust risk premiums

#### Scenario: Idaho State Pack Application
- **GIVEN** an Idaho market context with in-migration and forest-interface wildfire risks
- **WHEN** `state_packs.apply("ID", context)` is called
- **THEN** the system SHALL apply ID-specific migration pattern adjustments
- **AND** forest-interface wildfire risk multipliers SHALL be applied
- **AND** walkable district development patterns SHALL influence supply constraints

#### Scenario: State Rule Pack Persistence
- **GIVEN** a state rule pack application
- **WHEN** the rule pack is applied to a context
- **THEN** the `state_rules` table SHALL store a snapshot of applied rules
- **AND** the snapshot SHALL include rule version, application timestamp, and affected parameters
- **AND** YAML configuration changes SHALL trigger new snapshots

#### Scenario: UI State Selector Integration
- **GIVEN** a user interface for market analysis
- **WHEN** a state is selected from CO/UT/ID dropdown
- **THEN** the system SHALL automatically pre-fill guardrails based on state rule pack
- **AND** risk cost calculations SHALL reflect state-specific peril patterns
- **AND** winterization cost estimates SHALL include state-specific adders

#### Scenario: State Rule Pack Validation
- **GIVEN** an applied state rule pack
- **WHEN** validation tests are executed
- **THEN** the system SHALL verify that guardrails are mutated as expected
- **AND** risk costs SHALL reflect state-specific peril adjustments
- **AND** tax cadence SHALL align with state-specific requirements
- **AND** winterization cost adders SHALL match state operational notes
