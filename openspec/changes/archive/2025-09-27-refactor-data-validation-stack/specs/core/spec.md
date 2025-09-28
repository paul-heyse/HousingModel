## ADDED Requirements
### Requirement: Unified Data Validation Stack
The system SHALL standardise on a layered validation stack composed of Pydantic (configuration/runtime DTOs), Pandera (DataFrame and table schemas), and Marshmallow (external payload serialization) while removing the project’s dependence on Great Expectations.

#### Scenario: Pandera Guards Tabular Pipelines
- **WHEN** an ETL flow materialises a DataFrame destined for storage or downstream scoring
- **THEN** the flow SHALL invoke a Pandera schema that enforces column presence, dtypes, and business rule bounds equivalent to the prior Great Expectations suite before persisting or handing off the data

#### Scenario: Pydantic Protects Configuration and Runtime Contracts
- **WHEN** configuration objects or in-memory DTOs are created inside pipelines or services
- **THEN** they SHALL be defined and validated with Pydantic models, raising structured errors on contract violations without requiring Great Expectations wrappers

#### Scenario: Marshmallow Validates External Interfaces
- **WHEN** data is serialised to or from external APIs, files, or analyst-facing exports
- **THEN** Marshmallow schemas SHALL validate and serialise the payloads, replacing Great Expectations-driven serialization checks while preserving audit logs

#### Scenario: Great Expectations Dependency Removed
- **WHEN** the project dependencies and CI workflows are evaluated
- **THEN** Great Expectations SHALL no longer be required or invoked, and validation coverage SHALL be demonstrated via Pydantic, Pandera, and Marshmallow backed tests and documentation
