## Why
The repository now includes multiple functional engines (market scoring, jobs, supply, hazard/risk, amenity ROI, asset fit) but still relies on mocked data. `sources.yml` enumerates authoritative data feeds (Census ACS/BFS/BPS, BLS CES/QCEW, BEA, LEHD, NOAA, Zillow/Redfin, Socrata permits, etc.) that need to be mapped to these modules. A dedicated proposal is required to describe how each feed integrates into the ETL layer, populates the data store, and supports reporting and analytics.

## What Changes
- Define an ETL integration roadmap covering demographics/labor/macro, supply & permits, housing market, hazard/risk, amenities/membership, and operational sentiment feeds using the sources catalog.
- Specify ingestion responsibilities, storage conventions, lineage expectations, and module consumers for each source family.
- Align data cadences, caching, and validation suites (Great Expectations) with existing modules to ensure deterministic runs and reporting.

## Impact
- Affected specs: `etl` (new integration requirements).
- Affected code (future work): `src/aker_core/etl/*`, data access layers under `aker_data`, Prefect/flow orchestration, reporting exports.
