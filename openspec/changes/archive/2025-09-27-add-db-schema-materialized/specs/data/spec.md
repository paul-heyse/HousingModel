## ADDED Requirements
### Requirement: Materialized Tables for Analytics
The system MUST provide materialized tables for frequently queried analytical data to improve query performance.

#### Scenario: Market analytics table
- **WHEN** querying market performance metrics
- **THEN** a materialized table `market_analytics` provides pre-computed metrics
- **AND** includes aggregated data from multiple source tables
- **AND** is updated on a scheduled basis

#### Scenario: Asset performance table
- **WHEN** analyzing asset performance across markets
- **THEN** a materialized table `asset_performance` provides computed metrics
- **AND** includes scoring data and market context
- **AND** supports efficient filtering and aggregation

#### Scenario: Table refresh scheduling
- **WHEN** source data is updated
- **THEN** materialized tables are refreshed on a configurable schedule
- **AND** refresh operations are logged with performance metrics

### Requirement: Database Views for Complex Joins
The system MUST provide database views for optimized complex join operations.

#### Scenario: Market supply view
- **WHEN** joining market and supply data
- **THEN** a view `market_supply_joined` provides the joined result
- **AND** includes all relevant columns from both tables
- **AND** is optimized for common query patterns

#### Scenario: Asset scoring view
- **WHEN** joining asset and scoring data
- **THEN** a view `asset_scoring_joined` provides comprehensive asset analysis
- **AND** includes pillar scores and market context
- **AND** supports complex analytical queries

#### Scenario: Cross-table analytics view
- **WHEN** performing cross-table analytics
- **THEN** views provide efficient access to multi-table relationships
- **AND** maintain referential integrity across joined data

### Requirement: Referential Integrity Enforcement
The system MUST enforce referential integrity through foreign key constraints.

#### Scenario: Market relationships
- **WHEN** inserting market data
- **THEN** foreign key constraints ensure data consistency
- **AND** cascade operations maintain referential integrity
- **AND** constraint violations are properly handled

#### Scenario: Asset relationships
- **WHEN** managing asset data
- **THEN** foreign key constraints link assets to markets and other entities
- **AND** ensure data consistency across related tables
- **AND** prevent orphaned records

#### Scenario: Score relationships
- **WHEN** updating scoring data
- **THEN** foreign key constraints maintain links to source data
- **AND** ensure scoring integrity across the system

### Requirement: Great Expectations Data Validation
The system MUST integrate Great Expectations for data type and range validation.

#### Scenario: Numeric range validation
- **WHEN** validating numeric columns
- **THEN** Great Expectations checks ensure values are within expected ranges
- **AND** out-of-range values are flagged for review
- **AND** validation results are logged and reported

#### Scenario: Data type validation
- **WHEN** processing imported data
- **THEN** Great Expectations validates data types match schema expectations
- **AND** type mismatches are corrected or flagged
- **AND** validation passes enable data processing

#### Scenario: Constraint validation
- **WHEN** enforcing business rules
- **THEN** Great Expectations validates constraint satisfaction
- **AND** constraint violations are logged with context
- **AND** validation failures trigger appropriate actions

### Requirement: Table Optimization for Analytics
The system MUST optimize table structures for analytical workloads.

#### Scenario: Partitioning strategy
- **WHEN** designing large tables
- **THEN** appropriate partitioning strategies are implemented
- **AND** time-based partitioning for temporal data
- **AND** location-based partitioning for spatial data

#### Scenario: Indexing strategy
- **WHEN** optimizing query performance
- **THEN** appropriate indexes are created for common query patterns
- **AND** composite indexes for multi-column filters
- **AND** spatial indexes for geometry columns

#### Scenario: View optimization
- **WHEN** creating database views
- **THEN** views are optimized for read performance
- **AND** avoid unnecessary joins and aggregations
- **AND** provide efficient access to analytical data
