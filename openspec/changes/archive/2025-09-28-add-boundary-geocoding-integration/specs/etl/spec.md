## ADDED Requirements
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
