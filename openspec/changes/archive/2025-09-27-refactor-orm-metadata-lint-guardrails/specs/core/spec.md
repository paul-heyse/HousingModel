## ADDED Requirements
### Requirement: ORM Metadata Governance
The system SHALL centralize SQLAlchemy metadata management so each declarative model shares a single registry/Base, preventing duplicate table registration and ensuring deterministic metadata state during tests and runtime.

#### Scenario: Single Declarative Base
- **WHEN** any module imports ORM models
- **THEN** the models SHALL register with a shared declarative Base/registry and re-imports SHALL NOT raise duplicate table exceptions

#### Scenario: Duplicate Table Detection
- **WHEN** a developer attempts to register a table name that already exists in metadata
- **THEN** the system SHALL surface a clear error (lint/test failure) before runtime execution

#### Scenario: Metadata Health Check In CI
- **WHEN** the test suite executes
- **THEN** a metadata health check SHALL confirm that table names are unique and mapped classes align with the canonical registry

### Requirement: Lint & CI Guardrails
The codebase SHALL maintain a zero-warning Ruff baseline with automated enforcement so imports stay sorted, unused symbols are removed, and lint failures block CI alongside tests.

#### Scenario: Ruff Clean Run Required
- **WHEN** CI or pre-commit hooks run Ruff
- **THEN** the lint step SHALL pass without outstanding violations and SHALL fail the pipeline when new issues are introduced

#### Scenario: Developer Tooling Updated
- **WHEN** a contributor runs the documented tooling (`pre-commit`, `make lint`, or equivalent)
- **THEN** Ruff auto-fix (safe rules) SHALL execute, import order SHALL be normalized, and configuration SHALL match project conventions

#### Scenario: Documentation Reflects Lint Policy
- **WHEN** engineers follow the contributor guide
- **THEN** the documentation SHALL state lint expectations, remediation workflow, and zero-warning policy so contributors can resolve issues locally before submitting changes
