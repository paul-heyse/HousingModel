## ADDED Requirements
### Requirement: DATA-001 SQLAlchemy Models And Alembic Migrations
The system SHALL provide typed SQLAlchemy ORM models for all core domain tables with geospatial fields where applicable and manage schema evolution via Alembic migrations. Production SHALL use PostgreSQL with PostGIS; development MAY use SpatiaLite with feature parity for non-critical geospatial operations.

#### Scenario: ORM Models Cover Core Domain Entities
- **WHEN** developers import `aker_data.models`
- **THEN** classes for Markets, pillar tables (supply/jobs/urban/outdoors), PillarScores, Assets, AssetFit, DealArchetype, AmenityProgram, RiskProfile, OpsModel, Runs, and Lineage SHALL be available with explicit columns and types

#### Scenario: Migrations Create And Evolve Schema
- **WHEN** Alembic `upgrade` is executed on an empty database
- **THEN** all tables, constraints, and geospatial extensions required by the ORM SHALL be created successfully
- **AND** **WHEN** `downgrade` is executed
- **THEN** the schema SHALL roll back cleanly without orphan artifacts

#### Scenario: PostGIS In Production, SpatiaLite In Dev
- **GIVEN** a production DSN pointing to PostgreSQL with PostGIS enabled
- **WHEN** models are created and migrations applied
- **THEN** geometry/geography columns SHALL be created using PostGIS types
- **AND** **GIVEN** a dev DSN pointing to SpatiaLite
- **THEN** equivalent tables SHALL be created with spatial columns mapped to SpatiaLite-compatible types or fallbacks sufficient for development workflows

#### Scenario: CRUD Smoke Tests Succeed
- **WHEN** inserting, querying, updating, and deleting representative rows for the core entities
- **THEN** operations SHALL succeed and round-trip types (including spatial) where supported
