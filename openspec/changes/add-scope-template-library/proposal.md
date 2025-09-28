## Why
Many portfolio decisions require consistent, comparable ROI analysis across recurring scopes of work. Today, ROI and payback are computed ad‑hoc, with inconsistent assumptions about costs, lifts, downtime, and baselines. A standardized scope template library and an ROI ladder (ranker) will make decisions faster, auditable, and reproducible.

## What Changes
- Add a new capability: Deal Scope Template Library and ROI Ladder
  - `deal_archetype` schema to define scope templates: cost inputs, expected lift/savings, downtime, lifetime, and metadata.
  - Python API: `deal.rank_scopes(asset_id, scopes=[...]) -> list[RankedScope]` computing ROI, payback, and viability flags and returning a ranked list.
  - Payback guards and ROI thresholds: filter out scopes that do not meet configured limits.
  - Deterministic tie‑break rules (e.g., higher ROI, then lower downtime, then lower cost).
- Add ETL inputs that improve accuracy of ROI:
  - Energy rates/tariffs by site/region and time.
  - Labor and material cost indices by region/quarter.
  - Baseline performance/utilization metrics per asset (from materialized tables).
  - Downtime cost rates by asset category.
  - Optional vendor quote ingestion to override template costs.

No breaking API changes are introduced.

## Impact
- Affected specs: `deal` (ADDED), `etl` (ADDED connectors supporting deal inputs)
- Affected code: new domain module for deal ranking (module name TBD), integration with existing data lake/materialized metrics
- Testing: scenario‑based ordering and payback enforcement; Great Expectations checks for ETL inputs

## Out of Scope
- Multi‑period cash flow modeling or NPV/IRR beyond simple annual savings and payback
- Automated scheduling/portfolio optimization (selection under budget)

## Open Questions
- Should ROI thresholds be global, per‑portfolio, or per‑archetype? (default: global with per‑archetype override)
- Minimum data freshness for ETL inputs (default: quarterly for indices, monthly for energy rates)

