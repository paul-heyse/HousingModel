## ADDED Requirements

### Requirement: 15-Minute Accessibility Analysis Engine
The system SHALL provide comprehensive 15-minute accessibility analysis for urban convenience evaluation, calculating POI and transit accessibility within walkable and bikeable distance thresholds.

#### Scenario: POI Counting Within Isochrones
- **GIVEN** precomputed 15-minute isochrones (walk and bike) and a comprehensive POI dataset
- **WHEN** `urban.poi_counts(isochrones, pois)` is called with categorized POI data
- **THEN** the function SHALL count POIs by category within each isochrone
- **AND** return separate counts for walk_15_ct, bike_15_ct for each POI type (grocery, pharmacy, K-8, urgent_care)
- **AND** ensure reproducible results using fixed POI dataset for regression testing

#### Scenario: Transit Stop Accessibility
- **GIVEN** GTFS transit feed data and 15-minute transit access isochrones
- **WHEN** calculating transit accessibility
- **THEN** the system SHALL count transit stops within 15-minute transit sheds
- **AND** differentiate by transit mode (bus, rail, light rail) and service frequency
- **AND** populate `market_urban.transit_ct` with normalized transit accessibility scores

#### Scenario: Isochrone Generation Standards
- **GIVEN** population center points and street network data
- **WHEN** generating 15-minute accessibility isochrones
- **THEN** the system SHALL use standard speeds: 4.8 km/h for walking, 15 km/h for cycling
- **AND** account for elevation and street type impedance factors
- **AND** validate isochrone accuracy against known benchmarks

#### Scenario: POI Data Quality and Classification
- **GIVEN** OSM POI data with varying quality and completeness
- **WHEN** processing POI data for accessibility analysis
- **THEN** the system SHALL classify POIs into standard categories (grocery, pharmacy, education, healthcare)
- **AND** apply data quality filters and confidence scoring
- **AND** handle missing or ambiguous POI classifications

### Requirement: Urban Connectivity and Walkability Assessment
The system SHALL analyze urban connectivity through intersection density calculation and bikeway network assessment for comprehensive walkability and bikeability evaluation.

#### Scenario: Intersection Density Calculation
- **GIVEN** street network data for an urban area
- **WHEN** calculating intersection density
- **THEN** the system SHALL count intersections per square kilometer
- **AND** normalize by land area excluding water bodies and parks
- **AND** populate `market_urban.interx_km2` with density metrics

#### Scenario: Bikeway Network Connectivity Analysis
- **GIVEN** OSM bikeway data and street network graphs
- **WHEN** assessing bikeway connectivity
- **THEN** the system SHALL calculate network connectivity indices using graph theory
- **AND** measure giant component share and edge density for bikeability
- **AND** populate `market_urban.bikeway_conn_idx` with connectivity scores

#### Scenario: Street Network Analysis
- **GIVEN** OSM street network data with varying completeness
- **WHEN** processing for connectivity analysis
- **THEN** the system SHALL validate network topology and connectivity
- **AND** handle disconnected street segments and data quality issues
- **AND** apply appropriate graph algorithms for connectivity assessment

#### Scenario: Walkability Index Integration
- **GIVEN** intersection density and bikeway connectivity metrics
- **WHEN** calculating overall walkability
- **THEN** the system SHALL combine multiple connectivity factors
- **AND** apply weighting schemes for different urban form types
- **AND** provide walkability scores for comparative analysis

### Requirement: Retail Health and Market Dynamics Analysis
The system SHALL analyze retail health through vacancy rates, rent trends, and market dynamics for comprehensive retail ecosystem assessment.

#### Scenario: Retail Rent Trend Analysis
- **GIVEN** time series retail rent data from multiple sources
- **WHEN** `urban.rent_trend(df)` processes rent data
- **THEN** the function SHALL calculate quarter-over-quarter rent changes
- **AND** compute annualized rent growth rates
- **AND** populate `market_urban.retail_rent_qoq` with trend metrics

#### Scenario: Retail Vacancy Rate Assessment
- **GIVEN** retail vacancy data from local and national sources
- **WHEN** calculating retail health metrics
- **THEN** the system SHALL normalize vacancy rates across different market sizes
- **AND** identify vacancy trends and turning points
- **AND** populate `market_urban.retail_vac` with health indicators

#### Scenario: Retail Health Composite Scoring
- **GIVEN** rent trends and vacancy data
- **WHEN** calculating retail health
- **THEN** the system SHALL combine vacancy and rent metrics into composite scores
- **AND** apply different weightings for different retail types (neighborhood vs regional)
- **AND** provide health classifications (healthy, declining, distressed)

#### Scenario: Market Dynamics Analysis
- **GIVEN** retail performance data over time
- **WHEN** analyzing market dynamics
- **THEN** the system SHALL identify retail supply/demand imbalances
- **AND** detect market cycles and turning points
- **AND** provide early warning indicators for retail health changes

### Requirement: Daytime Population and Employment Analysis
The system SHALL analyze daytime population dynamics using employment data and geographic analysis for comprehensive urban activity assessment.

#### Scenario: Daytime Population Calculation
- **GIVEN** LODES/LEHD employment data and population center locations
- **WHEN** calculating daytime population
- **THEN** the system SHALL aggregate employment-based population within 1-mile buffers
- **AND** account for residential population adjustments
- **AND** populate `market_urban.daytime_pop_1mi` with normalized metrics

#### Scenario: Employment Density Analysis
- **GIVEN** employment data by industry sector
- **WHEN** analyzing employment patterns
- **THEN** the system SHALL calculate employment density by sector
- **AND** identify employment clusters and concentrations
- **AND** assess impact on daytime population and urban activity

#### Scenario: Geographic Buffer Analysis
- **GIVEN** population center points and employment data
- **WHEN** creating 1-mile analysis buffers
- **THEN** the system SHALL handle buffer overlap and deduplication
- **AND** ensure consistent geographic coverage across MSAs
- **AND** validate buffer accuracy against ground truth data

#### Scenario: Temporal Population Dynamics
- **GIVEN** employment schedules and commuting patterns
- **WHEN** analyzing temporal population changes
- **THEN** the system SHALL model peak daytime population periods
- **AND** identify temporal patterns in urban activity
- **AND** provide insights for urban planning and development

### Requirement: Urban Convenience Database Schema
The system SHALL persist comprehensive urban convenience metrics in a robust `market_urban` table with full geospatial and temporal support for urban analysis.

#### Scenario: Comprehensive Urban Metrics Storage
- **GIVEN** calculated 15-minute access, connectivity, retail health, and daytime population metrics
- **WHEN** persisting to database
- **THEN** the `market_urban` table SHALL store all metrics with appropriate data types
- **AND** include `msa_id`, `data_vintage`, `calculation_timestamp`, and source metadata
- **AND** support geospatial storage for isochrones and accessibility analysis

#### Scenario: Geospatial Data Integration
- **GIVEN** isochrone geometries and POI locations
- **WHEN** storing urban accessibility data
- **THEN** the system SHALL support PostGIS geometry storage
- **AND** enable spatial queries for accessibility and proximity analysis
- **AND** maintain coordinate reference system consistency

#### Scenario: Data Integrity and Quality Tracking
- **GIVEN** urban metrics being inserted
- **WHEN** database constraints are enforced
- **THEN** POI counts SHALL be non-negative integers
- **AND** connectivity indices SHALL be valid floats in expected ranges
- **AND** retail metrics SHALL have appropriate data type constraints
- **AND** all geospatial data SHALL have valid geometry and CRS

#### Scenario: Performance Optimization for Urban Queries
- **GIVEN** the `market_urban` table with extensive urban data
- **WHEN** executing common analytical queries
- **THEN** the system SHALL use spatial indexes for geographic queries
- **AND** implement composite indexes for MSA and metric type queries
- **AND** optimize for dashboard loading with sub-second response times

#### Scenario: Audit Trail and Data Lineage
- **GIVEN** urban metrics stored in the database
- **WHEN** tracking data provenance and compliance
- **THEN** each record SHALL include data source references (OSM, GTFS, LODES)
- **AND** calculation methodology SHALL be version-controlled
- **AND** data quality flags SHALL be maintained for audit purposes
- **AND** the system SHALL support urban planning reporting requirements

### Requirement: Urban Metrics Validation Framework
The system SHALL implement comprehensive validation ensuring urban metric accuracy, reproducibility, and compliance with urban planning standards.

#### Scenario: POI Count Reproducibility Validation
- **GIVEN** a fixed POI dataset for regression testing
- **WHEN** `urban.poi_counts()` is executed multiple times
- **THEN** the function SHALL produce identical results across executions
- **AND** validation SHALL fail if POI fixtures change unexpectedly
- **AND** provide detailed reporting of any count discrepancies

#### Scenario: Cross-Source Urban Data Validation
- **GIVEN** urban metrics from multiple data sources
- **WHEN** cross-validating calculations
- **THEN** the system SHALL reconcile OSM, GTFS, and local data sources
- **AND** identify and flag data inconsistencies
- **AND** provide confidence scores for metric reliability

#### Scenario: Urban Planning Standards Compliance
- **GIVEN** urban metrics and planning standards
- **WHEN** validating against urban planning guidelines
- **THEN** the system SHALL ensure 15-minute accessibility follows standard methodologies
- **AND** connectivity metrics align with walkability research
- **AND** retail health indicators follow market analysis best practices

#### Scenario: Performance and Scalability Validation
- **GIVEN** large-scale urban analysis requirements
- **WHEN** testing with representative MSA datasets
- **THEN** the system SHALL meet performance requirements for all US MSAs
- **AND** spatial operations SHALL complete within acceptable time limits
- **AND** memory usage SHALL remain within reasonable bounds
