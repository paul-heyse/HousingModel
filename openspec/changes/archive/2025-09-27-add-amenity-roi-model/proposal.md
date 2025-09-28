## Why
Amenity ROI metrics (capex/opex/rent premium/retention delta/membership revenue) are referenced in project.md but we lack a codified evaluation surface, persistence schema, and supporting data feeds. Analysts need a repeatable way to score amenity packages, understand NOI impact, and ingest vendor/performance benchmarks.

## What Changes
- Define an Amenity ROI engine in core with `amenity.evaluate(asset_id, amenities=[...]) -> impacts` for rent premium, retention delta, ancillary revenue, and payback analytics.
- Specify persistence in `amenity_program` (per amenity/per asset) including capex, opex, ROI metrics, data vintage, and run metadata.
- Introduce ETL requirements for amenity performance benchmarks (vendor costs, utilization, membership uptake) and optional integrations (smart access, cowork, pet amenities) to enrich evaluations.
- Document tests/DoD ensuring positive premiums and retention lifts translate to higher NOI and that pipelines surface explainable outputs for reports/exports.

## Impact
- Affected specs: `core`, `etl`.
- Affected code: `src/aker_core/amenities/`, `src/aker_core/reporting/`, `aker_data` models/migrations (`amenity_program`), amenity benchmark ETL connectors.
