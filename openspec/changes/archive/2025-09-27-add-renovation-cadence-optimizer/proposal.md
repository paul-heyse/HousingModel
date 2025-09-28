## Why
The project specification in project.md references a "renovation cadence optimizer (units/week) under vacancy cap" as part of the operations model, but this optimization engine is not yet implemented. Property managers need a systematic way to schedule renovation work that minimizes vacancy impact while maximizing renovation velocity and smoothing downtime across the portfolio.

## What Changes
- Implement a renovation cadence optimization engine in core with `ops.optimize_cadence(units, downtime_wk, vacancy_cap) -> plan`
- Define persistence schema for `ops_model.cadence_plan` to store optimization results
- Create supporting data structures for renovation scheduling and constraint management
- Add validation tests ensuring constraint satisfaction and optimal scheduling under vacancy caps
- Document integration points with existing asset and operations models

**BREAKING**: None - this adds new optimization capability without modifying existing interfaces

## Impact
- Affected specs: `core` (operations optimization)
- Affected code: `src/aker_core/ops/`, data models for `ops_model.cadence_plan`
- New dependencies: None required (optimization can use standard libraries)
- Database migrations: New `ops_model` table with `cadence_plan` field
- Testing: Unit tests for constraint satisfaction, integration tests with asset data
