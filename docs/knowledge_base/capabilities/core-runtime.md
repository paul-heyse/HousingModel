# Capability: Core Runtime

## Objective
Provide deterministic, auditable execution of the Aker Property Model by coordinating configuration, run metadata, scoring utilities, and shared infrastructure used across every workflow.

## Key Outcomes
- Centralised settings (`aker_core.config.Settings`) and feature flag resolution for 12-factor deployments.
- Immutable run tracking with lineage logging through `aker_core.run.RunContext`.
- Reusable scoring and normalization helpers that uphold spec guarantees for market analysis.
- Shared primitives (cache, plugins, validation, logging) that upstream capabilities import instead of reimplementing.

## Architecture Snapshot
- **Entry Points**: `aker_core.config.Settings`, `aker_core.run.RunContext`, `aker_core.markets.score`, `aker_core.scoring.robust_minmax`.
- **Packages**: `src/aker_core/config.py`, `src/aker_core/run.py`, `src/aker_core/markets`, `src/aker_core/scoring.py`, `src/aker_core/cache.py`.
- **Dependencies**: Pydantic Settings, SQLAlchemy (runs & lineage tables), Prometheus client (optional metrics), Postgres/PostGIS for persistence.
- **Integrations**: Feature flags via environment variables; lineage logging writes to `runs`/`lineage` tables referenced by downstream dashboards.

## Operational Workflow
1. Load `Settings()` during process start; override defaults with `.env` and environment variables.
2. Wrap pipelines in `with RunContext(settings) as run:` to stamp run identifiers, seeds, and git metadata.
3. Execute scoring or analytics functions (e.g., `markets.score`, `robust_minmax`) using cached data and configured weights.
4. Persist outputs and lineage with attached `run_id`; expose Prometheus metrics if enabled.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| `runs` table | Tracks execution metadata | Per run | Created via `RunContext` on every orchestrated workflow.
| `lineage` table | Records dataset provenance | Per dataset read | Populated by `run.log_lineage` calls with dataset hash + URL.
| Cache directory | Stores intermediate parquet/json artifacts | On demand | Paths resolved from `AKER_CACHE_PATH` or defaults.

## Validation & QA
- `tests/core/test_config.py` verifies precedence rules and serialization without secrets.
- `tests/core/test_run_context.py` ensures run metadata propagation and deterministic seeds.
- `tests/test_market_score_composer.py` and `tests/core/test_pillar_scoring.py` cover weight composition and deterministic outputs.
- Property-based suite (`tests/core/test_normalization_properties.py`) enforces normalization invariants.

## Runbooks
- [Core Runtime](../runbooks/core-runtime.md)

## Change Log
- 2024-06-04 — Initial knowledge base entry created via `add-comprehensive-documentation`; links specs to runtime modules.

