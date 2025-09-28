## Why

Portfolio managers need real-time visibility into exposure concentrations and automated alerts when thresholds are breached. The current system lacks systematic monitoring of portfolio composition by strategy, geography, vintage, and other key dimensions, making it difficult to maintain mandate compliance and identify concentration risks proactively.

## What Changes

- **BREAKING**: New `portfolio` capability with exposure computation engine
- Add `portfolio.compute_exposures(positions)` API surface
- Implement exposure aggregation by multiple dimensions (strategy, state, MSA, submarket, vintage, construction type, rent band)
- Add configurable threshold-based alert system
- Create dashboard-ready exposure aggregates schema
- Integrate with existing market and asset data for geographic exposure analysis

## Impact

- Affected specs: New `portfolio` capability spec
- Affected code: New portfolio module, database schema updates, dashboard integration
- Risk: Changes portfolio data flow patterns, requires backfill of historical exposure data
- Migration: Existing portfolio analysis workflows will need to migrate to new API
