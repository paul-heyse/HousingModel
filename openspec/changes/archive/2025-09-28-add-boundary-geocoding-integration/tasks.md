## 1. Specification
- [x] 1.1 Capture boundary/geocoder integration requirements (TIGERweb, OpenAddresses, Microsoft footprints, Census Geocoder, OSM Nominatim, Mapbox) in `etl` delta.
- [x] 1.2 Document validation, lineage, caching, and module consumers for each source family.
- [x] 1.3 Validate change with `openspec validate add-boundary-geocoding-integration --strict`.

## 2. Implementation Planning (post-approval)
- [x] 2.1 Inventory API keys/rate limits and staging tables required for boundary/geocoder feeds.
- [x] 2.2 Sequence ETL connectors and Prefect flows, aligning with existing scheduling framework.
- [x] 2.3 Define acceptance criteria for geospatial QA (CRS, topology) and caching/offline operation.

## 3. Follow-up
- [x] 3.1 Update roadmap to link boundary/geocoder integration tasks to executing teams once scheduled.
