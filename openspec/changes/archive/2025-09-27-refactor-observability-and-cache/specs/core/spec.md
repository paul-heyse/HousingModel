## MODIFIED Requirements
### Requirement: Structured Logging
The system SHALL expose a typed `aker_core.logging.get_logger(__name__)` returning a structured logger that emits JSON events with contextual fields (e.g., `msa`, `ms`) for traceable operations **and SHALL provide Prometheus helpers (`generate_metrics`, `make_metrics_app`, `start_metrics_server`) with documented behaviour.**

#### Scenario: Market Scoring Log Includes Context
- **WHEN** `get_logger("scoring").info("scored_market", msa="DEN", ms=42)` is called
- **THEN** the emitted log SHALL be JSON containing the event name `scored_market` and the fields `msa` and `ms`

#### Scenario: Logging Helpers Support Prometheus Endpoints
- **WHEN** `generate_metrics()` or `make_metrics_app()` is invoked in an environment with Prometheus client
- **THEN** the helper SHALL return exposition content without repeated registry creation and SHALL raise a clear error if Prometheus is unavailable

### Requirement: Runtime Feature Flags
The feature flag system SHALL continue to resolve defaults, dotenv, and environment values in precedence order without behavioural changes from this refactor.

#### Scenario: Flag Resolution Remains Unchanged
- **WHEN** a feature flag is overridden via environment variables
- **THEN** `is_enabled()` SHALL reflect the environment value after logging optimizations

### Requirement: Cache Behaviour
The cache subsystem SHALL respect environment overrides (`AKER_CACHE_PATH`) and infer storage metadata (e.g., JSON vs Parquet) while exposing helper utilities for reading metadata.

#### Scenario: Cache Respects Environment Override
- **WHEN** `AKER_CACHE_PATH` is set and `Cache()` is constructed without a base path
- **THEN** artifacts SHALL be persisted beneath the override directory and metadata helper SHALL reflect the resolved path

#### Scenario: JSON Data Stores Metadata
- **WHEN** JSON-like data is stored without specifying `data_type`
- **THEN** the payload SHALL be saved under the inferred type with an adjacent metadata file indicating `data_type="json"`

### Requirement: Flow Orchestration
Prefect deployments SHALL be defined using supported APIs (Prefect 3 `flow.deploy()` / `flow.serve()`) and tested for serialization.

#### Scenario: Deployment Definitions Load
- **WHEN** deployments are instantiated in tests
- **THEN** each deployment SHALL expose a serializable representation without raising exceptions

### Requirement: Run Context Engine Management
The `with_run_context` decorator SHALL reuse database engines and session factories instead of recreating them for each invocation.

#### Scenario: Session Factory Reuse
- **WHEN** multiple tasks enter the run context within a flow
- **THEN** the underlying SQLAlchemy engine SHALL be reused (confirmed via test instrumentation) and run status SHALL persist even on meta-session commit errors
