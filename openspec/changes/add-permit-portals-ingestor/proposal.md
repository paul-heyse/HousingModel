## Why
Local government permit data is essential for housing market analysis but is scattered across thousands of municipal websites and APIs with inconsistent formats and access patterns. Without a standardized ingestion system, collecting this data requires manual processes and custom scrapers per jurisdiction. A pluggable permit portal ingestor enables automated, scalable collection of permit data across cities and states.

## What Changes
- Introduce `PermitsConnector` class with pluggable spiders and APIs per city/state.
- Implement 3-year rolling window data collection with configurable date ranges.
- Create standardized data models for permit records with dates, status, and metadata.
- Add rate limiting, caching, and error handling for robust data collection.
- Integrate with existing ETL orchestration and data lake storage.

## Impact
- Affected specs: etl/ingestion
- Affected code: `src/aker_core/permits/`, permit data ingestion flows, data lake storage.
