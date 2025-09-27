## Why
Urban accessibility analysis requires computing 15-minute walk and bike access to essential amenities (grocery stores, pharmacies, schools, transit stops, urgent care). Current approaches lack standardized, performant computation of isochrones using street networks. A dedicated isochrone engine using osmnx/networkx provides accurate, reproducible accessibility metrics essential for urban convenience scoring.

## What Changes
- Introduce `aker_geo.isochrones` module with network-based isochrone computation.
- Implement 15-minute access metrics using osmnx/networkx for walk and bike modes.
- Add optional OSRM/Valhalla integration for production-scale routing.
- Create standardized computation of amenity accessibility counts.
- Integrate with existing geospatial data and market scoring workflows.

## Impact
- Affected specs: geo/isochrones
- Affected code: `src/aker_geo/isochrones/`, accessibility computation, market scoring.
