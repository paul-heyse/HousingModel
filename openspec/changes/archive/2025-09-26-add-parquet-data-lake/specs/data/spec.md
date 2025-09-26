## ADDED Requirements
### Requirement: DATA-002 Parquet Data Lake Conventions
The system SHALL provide a partitioned Parquet data lake at `/lake/{dataset}/` with Hive-style `as_of=YYYY-MM` partitioning for raw and cleaned datasets, supporting schema evolution and efficient querying via `aker_data.lake.write()` and `aker_data.lake.read()` functions.

#### Scenario: Write Partitioned Dataset
- **GIVEN** a DataFrame with columns including partition columns
- **WHEN** `aker_data.lake.write(df, "acs_income", as_of="2025-06", partition_by=["state"])` is called
- **THEN** files SHALL be written to `/lake/acs_income/as_of=2025-06/state=XX/*.parquet` with appropriate partitioning

#### Scenario: Read Dataset With Time Filter
- **GIVEN** a dataset with multiple as_of partitions
- **WHEN** `aker_data.lake.read("acs_income", as_of="2025-06")` is called
- **THEN** only data from the `as_of=2025-06` partition SHALL be returned

#### Scenario: Schema Evolution Tolerated
- **GIVEN** an existing dataset with schema v1
- **WHEN** new data with schema v2 (added columns) is written to a new as_of partition
- **THEN** reading from v1 partition SHALL succeed and reading from v2 partition SHALL return the new columns

#### Scenario: Great Expectations Integration
- **WHEN** writing a dataset
- **THEN** the configured Great Expectations suite SHALL be executed against the data
- **AND** validation results SHALL be logged to the lineage system

#### Scenario: Partition-Aware Reading With Filters
- **WHEN** `aker_data.lake.read("acs_income", filters={"state": "CA"})` is called
- **THEN** only partitions matching the filter SHALL be read, improving performance
