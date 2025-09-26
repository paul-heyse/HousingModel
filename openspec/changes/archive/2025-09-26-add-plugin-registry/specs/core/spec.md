## ADDED Requirements
### Requirement: Hexagonal Port Definitions
The system SHALL define abstract port interfaces for MarketScorer, AssetEvaluator, DealArchetypeModel, and RiskEngine in `aker_core.ports` so core workflows depend on contracts rather than concrete implementations.

#### Scenario: Port Defines Required Methods
- **WHEN** a developer inspects `MarketScorer`
- **THEN** the interface SHALL document required inputs and outputs for scoring markets

### Requirement: Plugin Registry
The system SHALL provide a registry in `aker_core.plugins` that supports registering adapters by name, retrieving them, and discovering entry-point declared plugins at startup.

#### Scenario: Register And Retrieve Adapter
- **WHEN** `plugins.register("census_acs", CensusACSConnector)` is called
- **THEN** `plugins.get("census_acs")()` SHALL return an instance of `CensusACSConnector`

#### Scenario: Entry Point Discovery Loads Plugins
- **WHEN** plugins are declared via Python entry points
- **THEN** `plugins.discover()` SHALL load and register each adapter without code changes

### Requirement: Testability Through Hot Swapping
Adapters SHALL be hot-swappable in tests by registering test doubles without mutating production wiring.

#### Scenario: Test Registers Stub Adapter
- **WHEN** a test registers a stub with `plugins.register("census_acs", StubConnector, override=True)`
- **THEN** subsequent calls to `plugins.get("census_acs")()` SHALL return the stub implementation for the duration of the test
