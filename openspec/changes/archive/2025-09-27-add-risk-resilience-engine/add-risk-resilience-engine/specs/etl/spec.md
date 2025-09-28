## ADDED Requirements
### Requirement: Hazard Dataset Pipelines
The ETL system SHALL ingest and refresh hazard datasets required for risk multipliers, including wildfire wildland-urban interface (WUI), hail frequency, snow load, water stress/drought, and policy/regulatory risk, producing spatially joined tables keyed to markets and assets with full lineage.

#### Scenario: Wildfire WUI Ingestion
- **GIVEN** publicly available WUI shapefiles (e.g., USDA Forest Service, state-level WUI layers)
- **WHEN** the ETL flow executes `etl.hazards.load_wildfire_wui`
- **THEN** the pipeline SHALL download the latest data, project it to EPSG:4326, dissolve as needed, compute severity indices (0–100) by intersecting with asset polygons/MSA boundaries, and persist outputs with `data_vintage`, `source_url`, and lineage rows tied to the active `run_id`

#### Scenario: Hail And Convective Storm Metrics
- **GIVEN** NOAA Storm Events (hail) and/or CoreLogic/Verisk hail swath datasets (licensed)
- **WHEN** `etl.hazards.load_hail_frequency` runs
- **THEN** the ETL SHALL aggregate hail counts/intensity over rolling 5-year windows, normalize to 0–100 severity per geography, and expose deductible guidance (e.g., % of TIV) for underwriting, capturing licensing metadata when commercial feeds are used

#### Scenario: Snow Load Surfaces
- **WHEN** `etl.hazards.load_snow_load` executes against NRCS Snow Load tables or ASCE 7 ground snow load rasters
- **THEN** values SHALL be interpolated to asset coordinates, converted to structural load categories, and stored alongside confidence intervals for engineering review

#### Scenario: Water Stress And Drought
- **GIVEN** datasets such as WRI Aqueduct, US Drought Monitor, and state-level water rights constraints
- **WHEN** the ETL flow processes water stress sources
- **THEN** it SHALL calculate composite scarcity indices, identify tap moratoria flags, and provide data sufficient for multiplier calibration, with refresh cadences documented (monthly for drought, annual for structural indices)

#### Scenario: Policy And Regulatory Risk
- **WHEN** `etl.hazards.load_policy_risk` collects policy datasets (rent control zones, insurance regulation, construction moratoria)
- **THEN** the pipeline SHALL transform sources into binary or graded severity scores, join to markets/assets, and store effective dates plus citations so that the risk engine can trace policy adjustments

#### Scenario: Data Quality And Monitoring
- **WHEN** hazard ETL flows run
- **THEN** Great Expectations suites SHALL validate schema, range bounds, and spatial coverage; anomalies SHALL trigger alerts/metrics; and parquet extracts SHALL be versioned in the data lake with partitioning by hazard and as-of date

#### Scenario: Downstream Availability
- **WHEN** risk computations or dashboards request hazard data
- **THEN** the ETL outputs SHALL be accessible through the data access layer (`aker_data.hazards`) with documented APIs, materialized summary tables, and caching hooks to support both batch and interactive workloads
