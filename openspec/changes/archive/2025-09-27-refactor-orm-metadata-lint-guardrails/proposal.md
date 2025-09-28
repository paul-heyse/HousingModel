## Why
SQLAlchemy declarative models are registering duplicate tables and breaking the global metadata during test collection, and the Ruff report shows hundreds of unresolved lint violations. Both problems block CI automation and violate our core spec expectations for deterministic runs and code quality.

## What Changes
- Consolidate SQLAlchemy declarative configuration so every mapped class shares a single registry/Base and enforce metadata checks that fail fast on duplicate table names.
- Establish lint guardrails (auto-sorted imports, unused symbol detection, max-fix backlog) with tooling hooks so Ruff can run clean in CI and locally.
- Update contributor guidance and automation (pre-commit/CI) to require green lint/test gates before merges.

## Impact
- Affected specs: `core` (new requirements for ORM metadata governance and lint/CI guardrails).
- Affected code: `aker_data.models*`, `aker_core/ops` packages, lint configs (`pyproject.toml`, pre-commit), CI scripts, developer docs.
