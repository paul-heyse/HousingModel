## ADDED Requirements
### Requirement: Data Source Integration Roadmap
The ETL layer SHALL incorporate the catalogued external data sources defined in `sources.yml` so each existing module (market scoring, jobs, supply, risk, amenities, asset fit) runs against authoritative data with documented cadence, lineage, and validation.

#### Scenario: Demographics, Labor & Macro Feeds
- **GIVEN** the feeds `census_acs`, `bls_timeseries`, `bls_qcew`, `bea_regional`, `census_bfs`, and `lehd_lodes`
- **WHEN** ETL pipelines execute `etl.demographics.load_acs`, `etl.jobs.load_bls_timeseries`, `etl.jobs.load_qcew`, `etl.macro.load_bea_income`, `etl.business.load_bfs`, and `etl.jobs.load_lodes`
- **THEN** data SHALL be extracted to parquet partitions keyed by `as_of`, joined to MSAs/counties, validated with Great Expectations suites (coverage, numeric ranges), and surfaced through `aker_data` accessors feeding the jobs/market scoring modules (`aker_jobs`, `aker_core/markets`)
- **AND** lineage SHALL record source URLs, vintages, and run IDs; cache TTL follows `defaults.cache_ttl` from `sources.yml`

#### Scenario: Housing Supply & Permits Feeds
- **GIVEN** feeds `census_bps`, `socrata_soda`, `arcgis_feature`, and `accela_civic`
- **WHEN** supply ETL pipelines (`etl.supply.load_bps`, `etl.permits.load_socrata`, `etl.permits.load_arcgis`, `etl.permits.load_accela`) run on their specified cadences
- **THEN** building permits, zoning, and entitlement datasets SHALL populate `market_supply`, `permit_events`, and related materialized views with spatial joins to assets/sites, providing inputs for the supply calculators and asset fit engine
- **AND** validations SHALL ensure permit counts are non-negative, geometries adhere to EPSG:4326, and offline cache snapshots respect the “CORE-005” TTL

#### Scenario: Housing Market Pricing Feeds
- **GIVEN** download-only feeds `zillow_research`, `redfin_datacenter`, and `apartment_list`
- **WHEN** ETL jobs fetch the latest rent/price CSV/TSV assets
- **THEN** datasets SHALL be normalized to monthly market panels (MSA/ZIP), stored in the data lake, and exposed to the market scoring composer and underwriting reports for comps, with ingestion metadata captured in lineage

#### Scenario: Hazard & Risk Feeds
- **GIVEN** hazard feeds listed in `sources.yml` (e.g., `noaa_hms_smoke`, `fema_nfhl`, `epa_airnow`, plus state wildfire layers via `arcgis_feature`)
- **WHEN** `etl.hazards` pipelines refresh these datasets
- **THEN** severity indices SHALL be computed and written to hazard staging tables powering the Risk Engine, with validation checks for severity bounds and spatial coverage; cache policies shall match provider guidance (hourly/daily refresh per source)

#### Scenario: Amenity, Mobility & Resident Experience Feeds
- **GIVEN** POI/review feeds (`osm_overpass`, `google_places`, `foursquare_places`) and mobility/amenity data (`openmobilitydata`, `gbfs`, etc.)
- **WHEN** ETL connectors fetch and normalize these feeds
- **THEN** amenity accessibility, urban convenience, and amenity ROI benchmarks SHALL ingest ratings/utilization to support `aker_core/urban` and the Amenity Engine, with licensing flags respected (disabled feeds require explicit configuration before execution)
- **AND** reports SHALL surface data provenance (source ID, timestamp) for any amenity-derived scores

#### Scenario: Run-Level Validation & Scheduling
- **WHEN** integration flows run on their respective cadences (monthly, quarterly, daily)
- **THEN** Prefect orchestration SHALL respect the timeouts/rate limits defined in `sources.yml`, ensure retries/backoff policies align with defaults, and emit Prometheus metrics for success/failure counts so the platform maintains deterministic, auditable pipelines
