## ADDED Requirements
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
