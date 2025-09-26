# Core Configuration

## Purpose
Provide a 12-factor compliant configuration system with feature flags so runtime behaviour stays auditable, reproducible, and free of hard-coded secrets.
## Requirements
### Requirement: Environment-First Application Settings
The system SHALL expose a typed `aker_core.config.Settings` object backed by pydantic-settings that loads defaults, an optional project `.env`, and environment variables in 12-factor precedence (environment > `.env` > defaults) while excluding secrets from source control.

#### Scenario: Environment Overrides Dotenv And Defaults
- **GIVEN** a default value and an entry in `.env`
- **WHEN** an environment variable with the same key is set before loading settings
- **THEN** `Settings()` SHALL resolve the environment value and report its source as `env`

#### Scenario: Dotenv Overrides Defaults When Environment Missing
- **GIVEN** a default value defined in code and a `.env` entry
- **WHEN** the matching environment variable is absent
- **THEN** `Settings()` SHALL return the `.env` value and report its source as `dotenv`

#### Scenario: Resolved Configuration Can Be Snapshotted Without Secrets
- **WHEN** the settings object is serialised for testing or diagnostics
- **THEN** only non-secret fields SHALL appear in the snapshot and the structure SHALL remain stable for regression tests

### Requirement: Runtime Feature Flags
The system SHALL provide `aker_core.flags.is_enabled(flag_name: str) -> bool` backed by the settings object to toggle behaviour without code changes and capture evaluated flags in `runs.config_json` for auditability.

#### Scenario: Flag Lookup Mirrors Settings Resolution
- **GIVEN** a flag default set to `false`
- **WHEN** an environment variable sets the flag to `true`
- **THEN** `is_enabled("EXAMPLE_FLAG")` SHALL return `True`

#### Scenario: Flag States Are Persisted With Run Metadata
- **WHEN** a pipeline run starts with evaluated settings
- **THEN** the resulting `runs.config_json` entry SHALL include the feature flag map used for that run

### Requirement: Typed External Dependency Settings
Every external dependency (APIs, storage, services) SHALL have a corresponding typed field within `aker_core.config.Settings`, documenting required parameters and ensuring zero secrets are hard-coded.

#### Scenario: Missing Required Dependency Field Raises Validation Error
- **GIVEN** a required API key field without default
- **WHEN** settings are loaded without providing the value via environment or `.env`
- **THEN** pydantic SHALL raise a validation error indicating the missing field

#### Scenario: Optional Dependencies Default Safely
- **WHEN** an optional integration is not configured
- **THEN** `Settings()` SHALL provide a safe default (e.g., `None` or feature flag disabled) and refrain from enabling the integration implicitly

### Requirement: Immutable Run Context
The system SHALL provide a context manager `aker_core.run.RunContext` that records git SHA, configuration hash, deterministic seed values, start/end timestamps, and assigns a unique `run_id` that is propagated to all outputs and persisted in the `runs` table.

#### Scenario: Run Context Captures Execution Metadata
- **WHEN** a pipeline executes within `with RunContext() as run`
- **THEN** the resulting `run` SHALL expose `run.id`, `run.git_sha`, `run.config_hash`, `run.seed`, `run.started_at`, and `run.finished_at` populated from the environment and configuration

#### Scenario: Outputs Carry Run Identifier
- **WHEN** a pipeline writes model outputs while the context is active
- **THEN** each output record SHALL include the assigned `run_id`

### Requirement: Deterministic Reruns
The system SHALL guarantee deterministic reruns when inputs and configuration are unchanged by reusing stored seeds and configuration hashes to validate outputs against previously recorded runs.

#### Scenario: Identical Inputs Produce Matching Hash
- **GIVEN** a prior run with recorded configuration hash and seeds
- **WHEN** the pipeline is rerun with the same inputs and configuration
- **THEN** the new run SHALL produce an identical output hash and be marked as such in the run log

### Requirement: Lineage Logging
The system SHALL expose `run.log_lineage(table, source, url, fetched_at, hash)` to persist dataset lineage rows in the `lineage` table for every external dataset consumed during the run.

#### Scenario: Lineage Entry Recorded For Data Source
- **WHEN** `run.log_lineage("markets", "census", "https://census.gov", fetched_at, hash)` is called
- **THEN** the `lineage` table SHALL receive a row tying the resource metadata to the active `run_id`

#### Scenario: Lineage Requires Active Run Context
- **WHEN** `log_lineage` is called outside an active run context
- **THEN** the system SHALL raise an error indicating that lineage logging requires an active `RunContext`

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

### Requirement: Structured Logging
The system MUST provide structured JSON logging with contextual fields and standardized event names.

#### Scenario: Pipeline execution logging
- **WHEN** a pipeline step executes
- **THEN** it emits structured JSON logs with event name, timestamp, and contextual fields

#### Scenario: Error logging with taxonomy
- **WHEN** an error occurs
- **THEN** it includes error code, category, and severity in the log structure

#### Scenario: Performance timing logs
- **WHEN** heavy operations complete
- **THEN** duration and resource usage are logged with appropriate event names

### Requirement: Prometheus Metrics Integration
The system MUST support optional Prometheus metrics collection with counters and histograms.

#### Scenario: Counter metrics
- **WHEN** operations complete
- **THEN** appropriate counters are incremented with relevant labels

#### Scenario: Histogram metrics for timing
- **WHEN** timed operations complete
- **THEN** duration histograms record the timing with appropriate buckets

#### Scenario: Metrics endpoint
- **WHEN** Prometheus scrapes the /metrics endpoint
- **THEN** it receives properly formatted metrics in exposition format
