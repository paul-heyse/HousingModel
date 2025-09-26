## ADDED Requirements
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
