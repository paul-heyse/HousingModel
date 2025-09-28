## Why
Risk multipliers (wildfire, hail, snow load, water stress, policy) are referenced in project.md but there is no implemented RiskEngine, schema, or data ingestion to translate hazards into underwriting adjustments. We need a spec that formalizes the computation API, database persistence, and ETL sources so underwriting and reports can consume consistent risk/resilience metrics.

## What Changes
- Define a core Risk Engine capability that computes peril-specific severity indices and 0.90–1.10 multipliers for markets and assets, persisting results in `risk_profile`.
- Specify Python surface (`risk.compute`, `RiskEntry`, `RiskEngine.apply_to_underwrite`) including bounds checks, monotonicity, and integration into reporting/export flows.
- Introduce ETL requirements for ingesting hazard datasets (wildfire WUI, hail, snow, drought/water stress, policy risk) with lineage, refresh cadence, and spatial joins to markets/assets.
- Document testing, DoD, and reporting hooks (unit/property tests, report integration, auditability).

## Impact
- Affected specs: `core`, `etl`.
- Affected code: `src/aker_core/risk/`, `src/aker_core/reporting/`, `aker_data` schemas/migrations, ETL pipelines for hazard data.
