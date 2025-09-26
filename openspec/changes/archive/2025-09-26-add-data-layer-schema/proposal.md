## Why
Implement a first-class data layer to persist and query all domain entities with spatial support, enabling deterministic, auditable runs across environments. We need typed models, migrations, and dev-friendly storage to match the project constraints (auditability, reproducibility, PostGIS-first).

## What Changes
- Introduce SQLAlchemy ORM models under `aker_data.models` for Markets, MarketSupply, MarketJobs, MarketUrban, MarketOutdoors, PillarScores, Assets, AssetFit, DealArchetype, AmenityProgram, RiskProfile, OpsModel, Runs, Lineage.
- Add Alembic migrations for schema creation and evolution, including PostGIS types (geometry/geography) and constraints.
- Support PostgreSQL + PostGIS for production; SpatiaLite for local development.
- Add minimal CRUD smoke tests and migration apply/rollback tests.

## Impact
- Affected specs: data/schema
- Affected code: `src/aker_data/models/*.py`, `alembic/` migrations, database configuration.
