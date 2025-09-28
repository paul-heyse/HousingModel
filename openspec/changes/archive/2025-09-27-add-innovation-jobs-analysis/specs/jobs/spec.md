## ADDED Requirements

### Requirement: Location Quotient Calculation
The system SHALL provide a `jobs.lq()` function that calculates location quotients for targeted NAICS sectors relative to national averages.

#### Scenario: Standard LQ Calculation
- **GIVEN** employment counts for a specific NAICS sector in a local area and nationally
- **WHEN** `jobs.lq(naics_counts)` is called with local and national employment data
- **THEN** the function SHALL return the location quotient: `(local_employment / local_total) / (national_employment / national_total)`
- **AND** the result SHALL be normalized such that national average LQ equals 1.0

#### Scenario: Multi-Sector Aggregation
- **GIVEN** employment data for multiple NAICS sectors (tech, health, edu, advanced mfg)
- **WHEN** `jobs.lq()` is called with sector-aggregated data
- **THEN** the function SHALL calculate LQ for each sector individually
- **AND** return a dictionary with sector names as keys and LQ values as values

#### Scenario: Per-100k Normalization
- **GIVEN** raw employment counts and population data
- **WHEN** calculating location quotients
- **THEN** the system SHALL normalize employment per 100,000 population
- **AND** ensure consistent units across all geographic areas

#### Scenario: Input Validation
- **GIVEN** invalid input data (negative values, mismatched geography)
- **WHEN** `jobs.lq()` is called
- **THEN** the function SHALL raise appropriate ValueError with descriptive message
- **AND** validate that local and national data cover the same time period

### Requirement: Compound Annual Growth Rate
The system SHALL provide a `jobs.cagr()` function that calculates 3-year compound annual growth rates for employment time series.

#### Scenario: Standard 3-Year CAGR
- **GIVEN** employment time series data for consecutive years
- **WHEN** `jobs.cagr(series, years=3)` is called
- **THEN** the function SHALL calculate: `(end_value / start_value)^(1/years) - 1`
- **AND** return the growth rate as a decimal (e.g., 0.05 for 5% growth)

#### Scenario: Variable Time Periods
- **GIVEN** employment series of different lengths
- **WHEN** `jobs.cagr()` is called with different `years` parameter
- **THEN** the function SHALL support 1-year, 3-year, and 5-year calculations
- **AND** validate that the series contains sufficient data points

#### Scenario: Edge Case Handling
- **GIVEN** time series with zero or negative starting values
- **WHEN** calculating CAGR
- **THEN** the function SHALL handle edge cases appropriately
- **AND** return meaningful results or appropriate error messages

#### Scenario: Time Series Validation
- **GIVEN** employment data with missing years or inconsistent intervals
- **WHEN** `jobs.cagr()` is called
- **THEN** the function SHALL validate data consistency
- **AND** raise errors for invalid time series

### Requirement: Net Migration Analysis (25-44 Age Group)
The system SHALL provide a `migration.net_25_44()` function that calculates net migration for the 25-44 age demographic.

#### Scenario: Basic Net Migration Calculation
- **GIVEN** inflow and outflow data for 25-44 age group in an MSA
- **WHEN** `migration.net_25_44(inflow, outflow)` is called
- **THEN** the function SHALL return `inflow - outflow` as net migration
- **AND** normalize the result per 1,000 population

#### Scenario: Geographic Aggregation
- **GIVEN** migration data at county or zip code level
- **WHEN** calculating MSA-level net migration
- **THEN** the function SHALL aggregate data to MSA boundaries
- **AND** handle boundary changes and geographic realignments

#### Scenario: Demographic Filtering
- **GIVEN** age-stratified migration data
- **WHEN** calculating 25-44 migration
- **THEN** the function SHALL filter to the 25-44 age range only
- **AND** exclude other age groups from the calculation

#### Scenario: Data Source Integration
- **GIVEN** migration data from Census/IRS sources
- **WHEN** processing migration flows
- **THEN** the system SHALL handle different data formats and vintages
- **AND** apply appropriate methodological adjustments

### Requirement: Expansion Event Tracking
The system SHALL track and analyze major expansion announcements in targeted sectors (universities, health, semiconductors, defense).

#### Scenario: Expansion Event Detection
- **GIVEN** news feeds, press releases, and API data
- **WHEN** processing expansion announcements
- **THEN** the system SHALL identify events in target sectors
- **AND** extract job creation estimates and timelines

#### Scenario: Sector Classification
- **GIVEN** expansion announcements from various sources
- **WHEN** categorizing by sector
- **THEN** the system SHALL classify as university, health, semiconductor, or defense
- **AND** handle ambiguous or multi-sector announcements

#### Scenario: Impact Quantification
- **GIVEN** identified expansion events
- **WHEN** calculating economic impact
- **THEN** the system SHALL estimate direct job creation
- **AND** apply appropriate multipliers for indirect effects

#### Scenario: Timeline Integration
- **GIVEN** expansion events with projected timelines
- **WHEN** integrating with market analysis
- **THEN** the system SHALL align expansion timing with market scoring periods
- **AND** handle delays and cancellations appropriately

### Requirement: Research Awards Analysis
The system SHALL analyze NIH, NSF, and DoD research funding awards per 100,000 population.

#### Scenario: Awards Data Integration
- **GIVEN** research funding data from NIH, NSF, and DoD APIs
- **WHEN** processing awards information
- **THEN** the system SHALL aggregate funding by institution and geography
- **AND** normalize awards per 100,000 population

#### Scenario: Geographic Mapping
- **GIVEN** institution-level award data
- **WHEN** aggregating to MSA level
- **THEN** the system SHALL map institutions to appropriate MSAs
- **AND** handle multi-location institutions appropriately

#### Scenario: Time-Based Analysis
- **GIVEN** historical award data
- **WHEN** calculating trends
- **THEN** the system SHALL support year-over-year comparisons
- **AND** identify funding pattern changes

#### Scenario: Sector-Specific Analysis
- **GIVEN** awards across different research areas
- **WHEN** categorizing by relevance to innovation sectors
- **THEN** the system SHALL identify awards relevant to tech, health, and defense
- **AND** calculate sector-specific funding metrics

### Requirement: Business Formation Statistics
The system SHALL integrate Census Business Formation Statistics to analyze startup activity and business dynamics.

#### Scenario: BFS Data Integration
- **GIVEN** Census BFS microdata
- **WHEN** processing business formation data
- **THEN** the system SHALL calculate formation rates by geography and sector
- **AND** normalize per 100,000 population

#### Scenario: Survival Rate Analysis
- **GIVEN** longitudinal BFS data
- **WHEN** analyzing business survival
- **THEN** the system SHALL calculate 1-year, 2-year, and 5-year survival rates
- **AND** identify patterns by sector and location

#### Scenario: Startup Density Metrics
- **GIVEN** business formation and establishment data
- **WHEN** calculating startup density
- **THEN** the system SHALL compute new business formations per existing establishment
- **AND** normalize by population and economic size

#### Scenario: Vintage Analysis
- **GIVEN** business formation data over time
- **WHEN** analyzing business vintages
- **THEN** the system SHALL track business age distributions
- **AND** calculate average business age by sector and location

### Requirement: Market Jobs Database Schema
The system SHALL persist all calculated innovation jobs and human capital metrics in a `market_jobs` table.

#### Scenario: Comprehensive Metrics Storage
- **GIVEN** calculated LQ, CAGR, migration, expansion, awards, and BFS metrics
- **WHEN** persisting to database
- **THEN** the `market_jobs` table SHALL store all metrics with appropriate data types
- **AND** include `msa_id`, `data_vintage`, and calculation metadata

#### Scenario: Data Integrity Constraints
- **GIVEN** metrics being inserted into `market_jobs`
- **WHEN** database constraints are enforced
- **THEN** LQ values SHALL be positive floats
- **AND** CAGR values SHALL be valid percentage decimals
- **AND** migration rates SHALL include proper population normalization

#### Scenario: Query Performance
- **GIVEN** the `market_jobs` table structure
- **WHEN** querying for market analysis
- **THEN** the system SHALL support efficient queries by MSA, time period, and metric type
- **AND** include appropriate indexes for common query patterns

#### Scenario: Data Lineage Tracking
- **GIVEN** metrics stored in `market_jobs`
- **WHEN** tracking data provenance
- **THEN** each record SHALL include source data references
- **AND** calculation methodology SHALL be documented
- **AND** data vintage SHALL be clearly marked
