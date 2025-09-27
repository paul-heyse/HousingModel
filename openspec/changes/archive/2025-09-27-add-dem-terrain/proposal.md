## Why
Topography and environmental constraints significantly impact housing development feasibility. Without automated analysis of slope constraints, waterway buffers, and overlay restrictions, site evaluation becomes manual and error-prone. A comprehensive DEM-based terrain analysis system provides accurate, automated constraint identification essential for supply-constrained market analysis.

## What Changes
- Introduce `aker_geo.terrain` module for DEM-based slope and constraint analysis.
- Implement slope percentage calculation for parcels using USGS DEM data.
- Create buffer analysis for waterways with configurable distance ranges (100–300 ft).
- Add overlay analysis for noise restrictions and viewshed constraints.
- Integrate with existing geospatial data and market supply analysis.

## Impact
- Affected specs: geo/terrain
- Affected code: `src/aker_geo/terrain/`, constraint analysis, market supply scoring.
