# Capability: ETL Pipelines

## Objective
Continuously ingest, normalize, and validate external datasets that power market, amenity, and risk analytics—keeping the model current with economic development activity, regulatory updates, and benchmark feeds.

## Key Outcomes
- Automated expansion intelligence via `aker_core.expansions.ExpansionsIngestor` with RSS/press-release parsing and entity extraction.
- Amenity, housing, hazard, and macroeconomic refreshers under `aker_core.etl.*` supplying normalized tables to the data lake.
- Config-driven feed registry (`src/aker_core/etl/sources.py`) that tracks cadence, credentials, and retry policies.
- Quality gates with Pandera/Great Expectations validators integrated into orchestration flows.

## Architecture Snapshot
- **Entry Points**: `ExpansionsIngestor.scan`, `etl.amenities.load_vendor_benchmarks`, `etl.housing.load_zillow_zori`, `etl.hazards.load_water_stress`.
- **Orchestration**: Prefect flows in `flows/` (e.g., `refresh_market_data.py`, `refresh_housing_market.py`, `refresh_hazard_metrics.py`) schedule pipeline execution and capture run context.
- **Storage**: Staging tables in Postgres + parquet exports via `aker_data.data_lake` helpers.
- **Dependencies**: `feedparser`, `beautifulsoup4`, `requests`, `geopandas`, vendor APIs (Redfin, Zillow, BLS, BEA).

## Operational Workflow
1. Prefect/automation triggers flow using environment-scoped `Settings()` secrets for API keys.
2. Load source manifests from `sources.yml` and iterate active feeds.
3. For each pipeline module, fetch raw content, parse into typed models (`ExpansionEvent`, hazard records, amenity benchmarks).
4. Run validation suites; on success, persist to data lake + warehouse and log lineage through `RunContext`.
5. Emit run metrics to Prometheus and raise alerts for failures or stale feeds.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| RSS/press releases | Expansion detection | Hourly | Configured in `sources_supplement.yml`; manual overrides allowed.
| BLS CES/QCEW | Labor metrics | Monthly | Downloaded via official APIs with retry + rate limiting.
| Zillow ZORI / Redfin | Rent & price trends | Weekly | Requires auth tokens stored in secrets backend.
| Vendor amenity benchmarks | Amenity ROI inputs | Quarterly | S3/HTTPS imports normalized via `load_vendor_benchmarks`.
| Hazard datasets (NOAA, Aqueduct, FEMA) | Risk overlays | Varies by dataset | Managed via hazard loaders with dataset-specific caching.

## Validation & QA
- `tests/test_expansions_ingestor.py` covers parsing, classification, and NER outputs.
- `tests/test_cache.py` and `tests/test_data_lake.py` ensure storage metadata and lineage tags persist.
- `tests/etl/test_boundary_geocoding_etl.py` / `tests/etl/test_jobs_pipeline.py` verify boundary + labor ETL flows (extend as new feeds are added).
- Prefect task hooks alert on stale feeds (>2× cadence) and validation failures.

## Runbooks
- [Etl Pipelines](../runbooks/etl-pipelines.md)

## Change Log
- 2024-06-04 — Established knowledge base entry outlining ETL asset coverage and lineage expectations.

