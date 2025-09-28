# Runbook: Geospatial Constraint Processing

## Purpose
Compute slope, buffer, and overlay constraints for target parcels or markets and persist results for supply scoring and underwriting.

## Preconditions
- `.venv` activated with geospatial stack installed (`rasterio`, `geopandas`, `shapely`, `pyproj`).
- DEM and hydro datasets accessible locally (`data/terrain/` cache) or via configured S3 bucket.
- PostGIS database reachable for persistence of processed constraints.
- Ensure GDAL/PROJ environment variables configured if running on macOS/Windows (`export PROJ_LIB=...`).

## Step-by-Step
1. **Download required DEM tiles**
   ```bash
   python - <<'PY'
   from pathlib import Path
   from aker_geo.terrain.sources import load_usgs_dem
   dem = load_usgs_dem('data/dem/denver_10m.tif')  # Update path to downloaded USGS raster
   print(dem.quality_report())
   PY
   ```
   Confirm DEM cached; repeated calls reuse local file.
2. **Compute slope statistics**
   ```bash
   python - <<'PY'
   import geopandas as gpd
   from aker_geo.terrain import slope_percent
   from aker_geo.terrain.sources import load_usgs_dem

   parcels = gpd.read_file('data/parcels/denver.gpkg')
   dem = load_usgs_dem('data/dem/denver_10m.tif')
   stats = slope_percent(parcels.geometry, dem=dem)
   print(stats.describe())
   PY
   ```
   Review statistics; slope >15° flagged as constrained per spec.
3. **Generate waterway buffers and classifications**
   ```bash
   python - <<'PY'
   import geopandas as gpd
   from aker_geo.terrain import waterway, assess_parcel_buffers

   waterways = gpd.read_file('data/hydro/nhd_subset.gpkg')
   buffers = waterway(waterways, distance_range=(100, 300))
   parcels = gpd.read_file('data/parcels/denver.gpkg')
   impact = assess_parcel_buffers(parcels, buffers)
   print(impact[['parcel_id', 'buffer_pct']].head())
   PY
   ```
   Persist results to PostGIS via `GeoDataFrame.to_postgis` if needed.
4. **Run overlay analysis**
   ```bash
   python - <<'PY'
   import geopandas as gpd
   from aker_geo.terrain import analyze_noise, analyze_viewshed, combine_overlay_results

   parcels = gpd.read_file('data/parcels/denver.gpkg')
   noise = gpd.read_file('data/overlays/noise_contours.gpkg')
   viewshed = gpd.read_file('data/overlays/viewshed.gpkg')
   noise_result = analyze_noise(parcels, noise)
   viewshed_result = analyze_viewshed(parcels, viewshed)
   combined = combine_overlay_results(noise_result, viewshed_result)
   print(combined.head())
   PY
   ```
5. **Compute unified constraint scores**
   ```bash
   python - <<'PY'
   import pandas as pd
   from aker_geo.terrain import compute_constraint_scores

   combined = pd.read_parquet('cache/constraints/denver_combined.parquet')  # Replace with path produced in prior steps
   scores = compute_constraint_scores(combined)
   print(scores.sort_values('constraint_score').head())
   PY
   ```
   Store scores to `market_supply` table using SQLAlchemy or data lake writer.

## Validation
- `pytest tests/test_geospatial.py tests/test_supply_integration.py`.
- Spot-check parcels in GIS viewer (QGIS or Mapbox) to confirm slope/buffer overlays align with expectations.
- Confirm persisted results include CRS metadata (`EPSG:4326` storage, `EPSG:3857` UI).

## Incident Response
- **DEM download failures**: Verify USGS endpoint reachable; set `USGS_API_KEY` if required. Retry with smaller bounding boxes.
- **CRS mismatch errors**: Use `GeoDataFrame.to_crs(4326)` before processing; update knowledge base if new projections introduced.
- **Performance issues**: Process parcels in batches (`geopandas.GeoDataFrame.iloc` chunks) or leverage raster tiling; document adjustments.

## References
- Capability brief: [capabilities/geo-services.md](../capabilities/geo-services.md)
- Spec: `openspec/specs/geo/spec.md`
- Data sources: `sources.yml` hazard entries.

