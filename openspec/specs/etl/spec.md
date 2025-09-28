# etl Specification

## Purpose
TBD - created by archiving change add-expansions-ingestor. Update Purpose after archive.
## Requirements
### Requirement: Press Release and RSS Feed Ingestion
The system MUST ingest and parse press releases and RSS feeds for economic development announcements.

#### Scenario: RSS Feed Processing
- **WHEN** `ExpansionsIngestor.scan(feeds)` is called
- **THEN** it processes RSS feeds from configured sources
- **AND** extracts article content and metadata
- **AND** identifies potential expansion announcements

#### Scenario: Press Release Parsing
- **WHEN** processing press releases
- **THEN** it extracts structured information from HTML/text content
- **AND** handles various press release formats and layouts
- **AND** preserves source attribution and publication dates

#### Scenario: Content Filtering
- **WHEN** scanning content sources
- **THEN** filters for expansion-related keywords and phrases
- **AND** prioritizes content likely to contain expansion announcements
- **AND** avoids processing irrelevant content

### Requirement: Named Entity Recognition for Expansion Data
The system MUST extract structured expansion data using simple NER techniques.

#### Scenario: Company Name Extraction
- **WHEN** processing expansion announcements
- **THEN** identifies and extracts company/organization names
- **AND** handles variations in company naming conventions
- **AND** validates extracted entities against known company lists

#### Scenario: Location and Geographic Data
- **WHEN** processing location information
- **THEN** extracts city, state, and facility location details
- **AND** normalizes location names and formats
- **AND** geocodes locations when possible

#### Scenario: Job Count and Expansion Details
- **WHEN** processing expansion announcements
- **THEN** extracts job creation numbers and expansion scope
- **AND** identifies timeline information (planned vs. completed)
- **AND** captures investment amounts when mentioned

### Requirement: Expansion Event Data Model
The system MUST provide a standardized data model for expansion events.

#### Scenario: Structured Expansion Data
- **WHEN** `ExpansionsIngestor.scan(feeds)` returns results
- **THEN** returns `[ExpansionEvent]` with standardized structure
- **AND** includes company, location, jobs, timeline, and source metadata
- **AND** provides confidence scores for extracted information

#### Scenario: Event Classification
- **WHEN** processing announcements
- **THEN** classifies events by type (new facility, expansion, relocation)
- **AND** identifies industry sectors and company sizes
- **AND** flags high-confidence vs. low-confidence extractions

#### Scenario: Data Enrichment
- **WHEN** creating expansion events
- **THEN** enriches with geographic and market context
- **AND** links to existing market and company data
- **AND** provides standardized categorization for analysis

### Requirement: Configurable Feed Sources and Parsing Rules
The system MUST support configurable RSS feeds and parsing rules.

#### Scenario: Feed Source Management
- **WHEN** configuring data sources
- **THEN** RSS feeds can be added/removed via configuration
- **AND** feed update frequencies are configurable
- **AND** failed feeds are automatically retried

#### Scenario: Parsing Rule Customization
- **WHEN** processing different content types
- **THEN** parsing rules adapt to source-specific formats
- **AND** custom extraction patterns can be defined
- **AND** rule effectiveness is monitored and reported

#### Scenario: Content Type Handling
- **WHEN** processing various content formats
- **THEN** handles HTML, plain text, and structured RSS content
- **AND** extracts relevant information regardless of format
- **AND** maintains consistent output structure

### Requirement: Data Quality and Validation
The system MUST validate extracted expansion data for quality and accuracy.

#### Scenario: Entity Validation
- **WHEN** extracting company and location names
- **THEN** validates against known entity databases
- **AND** flags suspicious or malformed extractions
- **AND** provides confidence scores for validation

#### Scenario: Numerical Data Validation
- **WHEN** extracting job counts and investment amounts
- **THEN** validates numerical ranges and reasonableness
- **AND** handles unit conversions (jobs, dollars, square feet)
- **AND** flags implausible values for manual review

#### Scenario: Temporal Consistency
- **WHEN** processing announcement dates
- **THEN** validates date ranges and chronological consistency
- **AND** handles various date formats and timezones
- **AND** identifies and flags temporal anomalies

### Requirement: Manual Override and Review Interface
The system MUST provide a user interface for manual review and correction of extracted data.

#### Scenario: Review Dashboard
- **WHEN** reviewing extracted expansion events
- **THEN** provides a dashboard showing extraction results
- **AND** highlights low-confidence extractions
- **AND** allows bulk review and approval workflows

#### Scenario: Manual Correction
- **WHEN** correcting extraction errors
- **THEN** allows manual override of extracted values
- **AND** preserves original extracted data for comparison
- **AND** tracks correction history and user actions

#### Scenario: Validation Rules
- **WHEN** applying validation rules
- **THEN** custom validation rules can be defined and applied
- **AND** rule violations trigger review workflows
- **AND** validation results inform confidence scoring

### Requirement: Integration with Existing Systems
The system MUST integrate with existing ETL and data storage systems.

#### Scenario: ETL Flow Integration
- **WHEN** running expansion data collection
- **THEN** executes as part of existing ETL orchestration
- **AND** supports both scheduled and manual execution
- **AND** integrates with data quality validation workflows

#### Scenario: Data Lake Storage
- **WHEN** storing expansion events
- **THEN** stores in data lake with proper partitioning
- **AND** maintains data lineage and metadata
- **AND** supports efficient querying and analysis

#### Scenario: Market Intelligence Integration
- **WHEN** processing expansion events
- **THEN** links to existing market and company data
- **AND** enriches with geographic and economic context
- **AND** provides standardized data for market scoring models

### Requirement: Performance and Scalability
The system MUST handle large volumes of content efficiently.

#### Scenario: Content Processing Scale
- **WHEN** processing high-volume RSS feeds
- **THEN** processes content in batches with progress tracking
- **AND** handles rate limiting and API quotas
- **AND** provides processing throughput metrics

#### Scenario: Memory and Resource Management
- **WHEN** processing large documents
- **THEN** manages memory usage efficiently
- **AND** streams large content when possible
- **AND** provides resource usage monitoring

#### Scenario: Error Recovery
- **WHEN** processing failures occur
- **THEN** implements retry logic with exponential backoff
- **AND** maintains processing state for resumption
- **AND** logs detailed error information for debugging

### Requirement: Monitoring and Alerting
The system MUST provide monitoring and alerting for data collection health.

#### Scenario: Processing Success Monitoring
- **WHEN** content processing completes
- **THEN** reports processing success rates and data volumes
- **AND** tracks extraction accuracy and confidence scores
- **AND** alerts on significant processing failures

#### Scenario: Data Freshness Monitoring
- **WHEN** monitoring data pipeline health
- **THEN** tracks content freshness and update frequency
- **AND** alerts when feeds become stale or unavailable
- **AND** provides visibility into processing pipeline status

#### Scenario: Quality Metrics
- **WHEN** evaluating extraction quality
- **THEN** tracks precision and recall metrics for NER
- **AND** identifies patterns in extraction errors
- **AND** provides actionable insights for improving accuracy

### Requirement: Amenity Benchmark ETL Pipelines
The ETL platform SHALL ingest and refresh amenity benchmark datasets (capex, opex, utilization, membership uptake, vendor pricing) that power the amenity ROI engine, producing normalized tables keyed to amenity codes and asset contexts.

#### Scenario: Vendor Cost & Utilization Benchmarks
- **GIVEN** partner/vendor APIs or CSV extracts providing amenity installation costs, operating expenses, and utilization rates (e.g., cowork lounges, pet spas, smart access)
- **WHEN** `etl.amenities.load_vendor_benchmarks` runs on the scheduled cadence
- **THEN** the pipeline SHALL normalize values to standard units (cost per door, opex per unit per month, utilization %), attach data vintages, and persist outputs with lineage entries tied to the active run

#### Scenario: Membership Revenue Data
- **GIVEN** membership or subscription data feeds (cowork passes, fitness memberships, parking subscriptions)
- **WHEN** `etl.amenities.load_membership_revenue` executes
- **THEN** the ETL SHALL aggregate monthly revenue per amenity, map to assets/MSAs, and expose distributions for the ROI engine with documented refresh cadence (e.g., monthly)

#### Scenario: Resident Sentiment & Retention Metrics
- **WHEN** `etl.amenities.load_retention_signals` ingests data from CRM/renewal systems or surveys
- **THEN** the pipeline SHALL compute retention deltas attributable to specific amenities, store confidence intervals, and surface these metrics to the evaluation engine

#### Scenario: Data Quality & Monitoring
- **WHEN** amenity ETL flows run
- **THEN** Great Expectations suites SHALL validate schema/ranges (non-negative costs, utilization within 0–1), anomalies SHALL trigger metrics/alerts, and parquet extracts SHALL be versioned by amenity code and `as_of` partition

#### Scenario: Downstream Access
- **WHEN** the amenity ROI engine requests benchmark inputs
- **THEN** the ETL outputs SHALL be available through `aker_data.amenities` data access helpers, supporting both batch computation and interactive what-if analysis

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

### Requirement: Boundary & Geocoding Source Integration
The ETL stack SHALL ingest and refresh the boundary and geocoding datasets listed in `sources_supplement.yml` (Census TIGERweb, OpenAddresses, Microsoft Global Building Footprints, Census Geocoder, OSM Nominatim, Mapbox Geocoding) so existing modules have authoritative geography coverage and address resolution.

#### Scenario: TIGERweb Boundary Extraction
- **WHEN** ETL pipelines call `etl.boundaries.load_tigerweb` for states, counties, tracts, places, and ZCTA layers
- **THEN** ArcGIS FeatureService responses SHALL be normalized into partitioned parquet tables (state/tract/place, CRS=EPSG:4326), validated for geometry integrity, and registered in the data lake for use by urban, risk, and reporting modules
- **AND** lineage SHALL capture the TIGERweb endpoint, vintage, and run ID

#### Scenario: Microsoft Building Footprints & OpenAddresses Ingestion
- **WHEN** the boundary ETL flow processes Microsoft Global Building Footprints and OpenAddresses batches
- **THEN** building polygons and address points SHALL be downloaded, deduplicated, and stored with geospatial validations (topology, CRS), providing optional inputs to amenity ROI, asset fit, and mapping exports

#### Scenario: Census Geocoder Integration
- **WHEN** geocoding services request standardized addresses
- **THEN** the Census Geocoder connector SHALL expose single-line, batch, and reverse geocoding utilities with caching and rate-limit handling, logging benchmark/vintage metadata so results are auditable

#### Scenario: Mapbox & OSM Nominatim (Optional Licensed Feeds)
- **WHEN** Mapbox or OSM Nominatim connectors are enabled
- **THEN** the ETL layer SHALL inject API tokens/user-agent requirements, respect usage policies, and cache results via the shared geocoding store to reduce provider load while providing fallbacks for amenity ROI and urban analytics

#### Scenario: Prefect Orchestration & Quality Gates
- **WHEN** boundary/geocoder flows run on their defined cadences (quarterly/annual for boundaries, on-demand for geocoding)
- **THEN** Prefect flows SHALL respect endpoints’ timeout/rate limits, record metrics, and trigger Great Expectations/pandera validations (boundary coverage, CRS, null rates) before downstream modules consume the data

