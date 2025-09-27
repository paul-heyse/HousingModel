## Why
The Aker Property Model requires a standardized market scoring system that combines supply constraints, innovation jobs, urban convenience, and outdoor access into a single composite score. Without a documented composer applying consistent weights (0.3 Supply + 0.3 Jobs + 0.2 Urban + 0.2 Outdoors), market comparisons become unreliable and difficult to audit. The composer must persist both 0–5 and 0–100 variants for different use cases while maintaining deterministic reproducibility.

## What Changes
- Introduce `aker_core.markets.composer.score()` function that accepts MSA identifiers or geometries and returns `MarketPillarScores` with both 0–5 and 0–100 composite scores.
- Implement the standard weighting scheme: 0.3×Supply + 0.3×Jobs + 0.2×Urban + 0.2×Outdoors.
- Add configurable weight overrides for scenario analysis and sensitivity testing.
- Persist composite scores and metadata in `pillar_scores` table with full audit trail.
- Provide deterministic computation with pillar weight swap regression tests.

## Impact
- Affected specs: core/markets
- Affected code: `src/aker_core/markets/`, market scoring workflows, `pillar_scores` persistence
