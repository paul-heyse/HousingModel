## Why
Operational performance impacts revenue. Converting reviews and NPS into a consistent Reputation Index enables transparent pricing and concession guardrails.

## What Changes
- Add `ops.reputation_index(reviews, nps) -> float` with deterministic scaling (0–100)
- Add `ops.pricing_rules(index)` returning guardrails for price and concessions
- Persist to `ops_model` with lineage (inputs, version, timestamp)
- ETL connectors for reviews and NPS APIs; optional benchmark feeds
- Tests with synthetic data verifying predictable index shifts

## Impact
- Specs affected: `ops` (index + rules), `etl` (reviews/NPS connectors)
- Code affected: `aker_core.ops` module, repository for `ops_model`, validation suites, CLI batch runner

## Non‑Goals
- Full dynamic pricing engine; this provides policy guardrails only
- UI implementation

## Open Questions
- Weighting of NPS vs. reviews sentiment by product/market
- Rolling window and decay for stale reviews
