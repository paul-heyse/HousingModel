# Capability: Geospatial Services

## Objective
Quantify environmental and terrain constraints—slope, waterways, noise, viewsheds—so supply modelling and underwriting incorporate physical development risk alongside regulatory overlays.

## Key Outcomes
- `aker_geo.terrain.DigitalElevationModel` loads USGS DEM tiles and exposes slope statistics via `terrain.slope_percent`.
- Buffer and overlay calculators (`terrain.waterway`, `terrain.analyze_noise`, `terrain.analyze_viewshed`) classify parcels by setback and overlay severity.
- Constraint scoring pipeline (`terrain.compute_constraint_scores`) harmonises slope, buffers, and overlays into market supply modifiers.
- CRS utilities (`aker_geo.crs.to_storage`, `to_ui`) keep spatial data aligned between storage (EPSG:4326) and UI (EPSG:3857).

## Architecture Snapshot
- **Entry Points**: `terrain.slope_percent`, `terrain.waterway`, `terrain.assess_parcel_buffers`, `terrain.compute_constraint_scores`.
- **Sources**: DEM downloads through `terrain.load_usgs_dem`, hydrography via `terrain.load_nhd_waterways`, local overlays ingested through ETL hazard pipelines.
- **Dependencies**: `rasterio`, `geopandas`, `shapely`, `pyproj`, PostGIS for persistence of processed geometries.
- **Integrations**: Outputs stored in `market_supply` tables and referenced by `MarketPillarScores` and state pack adjustments.

## Operational Workflow
1. Fetch DEM and hydro datasets defined in `sources.yml` if caches are stale.
2. Build `DigitalElevationModel` and compute slope stats for parcel geometries.
3. Generate buffer polygons for waterways and intersect with parcel footprints.
4. Apply overlay analyses (noise, viewshed) and combine scores via `compute_constraint_scores`.
5. Persist results and update lineage using active `RunContext`.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| USGS 3DEP DEM tiles | Elevation & slope | Quarterly or on-demand | Cached locally to reduce downloads; metadata recorded in lineage table.
| National Hydrography Dataset | Waterway buffers | Quarterly | Supports state/local overrides via ETL hazard loaders.
| FAA/municipal noise contours | Noise overlays | Annual | Imported via hazard ETL; path documented in runbook.
| Scenic corridor datasets | Viewshed overlays | Annual | Typically provided by state GIS portals; tracked per jurisdiction.

## Validation & QA
- `tests/test_geospatial.py` verifies CRS conversions, buffer generation, and slope statistics for representative parcels.
- `tests/test_outdoor_environmental.py` covers integration with outdoor pillar metrics.
- `tests/test_supply_integration.py` ensures supply scoring consumes constraint outputs with correct weighting.

## Runbooks
- [Geo Services](../runbooks/geo-services.md)

## Change Log
- 2024-06-04 — First knowledge base entry linking terrain utilities, overlay scoring, and validation coverage.

