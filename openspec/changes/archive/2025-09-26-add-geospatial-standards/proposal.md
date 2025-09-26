## Why
Geospatial data requires consistent coordinate reference systems (CRS) for accurate spatial analysis and visualization. Without standardized CRS handling, spatial operations can produce incorrect results, and data may not display properly in mapping applications. This change establishes geospatial standards and utilities for reliable spatial data processing.

## What Changes
- Introduce `aker_geo` module with CRS transformation utilities for EPSG:4326 (storage) and EPSG:3857 (UI).
- Implement geometry validation and correction for spatial data integrity.
- Add PostGIS SRID enforcement and geometry column validation.
- Provide coordinate transformation utilities for common spatial operations.
- Integrate with existing data lake and database operations for spatial data.

## Impact
- Affected specs: data/geospatial
- Affected code: `src/aker_geo/`, geometry column handling, spatial data ingestion and processing.
