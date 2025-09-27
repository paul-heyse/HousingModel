## Why
The Aker Property Model requires comprehensive, real-time data from multiple government and commercial sources to power market scoring, asset evaluation, and risk assessment. Without standardized, pluggable connectors, data collection becomes fragmented, unreliable, and difficult to maintain. This change establishes a unified connector system with explicit rate limits, vintage tracking, and automated data quality assurance.

## What Changes
- Introduce `aker_core.connectors` package with typed connectors for all major data sources.
- Implement explicit rate limiting and retry logic with exponential backoff.
- Add vintage tracking for data freshness and lineage management.
- Create standardized data models for each data source with validation.
- Integrate with existing cache, data lake, and ETL orchestration systems.

## Impact
- Affected specs: etl/connectors
- Affected code: `src/aker_core/connectors/`, data ingestion flows, lineage tracking.
