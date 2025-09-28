## ADDED Requirements

### Requirement: Deal Scope Template Library
The system SHALL provide a reusable library of deal scope templates describing cost, expected lift/savings, downtime, lifetime, and metadata, expressed via a `deal_archetype` schema. Templates MUST be composable and parameterizable (e.g., site, region factors; size multipliers).

#### Scenario: Define a scope template
- **WHEN** a template author creates a `deal_archetype` with fields for cost, lift, downtime, and lifetime
- **THEN** the system stores the template so it can be referenced by ranking

#### Scenario: Parameterize by asset context
- **WHEN** a template is applied to an `asset_id`
- **THEN** regional indices and baselines MAY adjust costs and expected lift

### Requirement: ROI Ladder (Scope Ranking)
The system SHALL compute ROI and payback for provided scopes against an asset baseline and SHALL return a ranked list ordered by ROI (desc), with tie‑break by downtime (asc) then cost (asc). The system MUST enforce a payback threshold and an optional minimum ROI threshold.

#### Scenario: Rank scopes by ROI
- **WHEN** `deal.rank_scopes(asset_id, scopes=[...])` is called with valid templates
- **THEN** the system computes ROI and payback and returns scopes sorted by ROI desc

#### Scenario: Enforce payback guard
- **WHEN** a scope’s payback exceeds the configured maximum
- **THEN** the scope is excluded from the ranked results

#### Scenario: Deterministic tie‑breaks
- **WHEN** two scopes have equal ROI
- **THEN** the one with lower downtime ranks higher; if equal, the lower cost ranks higher

### Requirement: Python Surface and Types
The system SHALL expose `deal.rank_scopes(asset_id, scopes=[...]) -> list[RankedScope]` and a `deal_archetype(...)` schema/type for templates. Types MUST include fields sufficient to compute ROI and payback and to apply ETL‑derived adjustments.

#### Scenario: Return typed results
- **WHEN** ranking completes
- **THEN** the result contains ROI, payback, downtime, viability flags, and traceable inputs per scope


