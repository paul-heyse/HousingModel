## Why
The supplemental source catalog introduces high-value boundary and geocoding datasets (Census TIGERweb, Census Geocoder, OSM Nominatim, Mapbox, OpenAddresses, Microsoft Global Building Footprints) that currently have no integration plan. Urban convenience, risk, asset fit, and report exports need authoritative boundaries and geocoding services. A dedicated proposal will define how these feeds join the ETL layer, power the existing modules, and align with the scheduling/caching practices recently established.

## What Changes
- Extend the ETL roadmap to cover boundary/geocoding sources from `sources_supplement.yml`, detailing ingestion patterns, data storage, and validation requirements.
- Provide orchestration guidance (Prefect flows, cadences, caching) and note API/usage constraints (keys, rate limits).
- Clarify module consumers (urban accessibility, amenity ROI, asset fit, reporting, geospatial staging) for each dataset.

## Impact
- Affected specs: `etl` (new requirements for boundaries & geocoding feeds).
- Affected code (future work): `src/aker_core/etl/*` boundary/geocoder connectors, geospatial staging tables, Prefect flows/deployments, report/UX analytics modules.
