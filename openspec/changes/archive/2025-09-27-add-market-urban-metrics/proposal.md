## Why

The Aker Property Model requires comprehensive urban convenience analysis to evaluate the "Urban Convenience" pillar, which constitutes 20% of the final market score. Currently, urban convenience scoring relies on fragmented, non-standardized metrics without proper 15-minute accessibility analysis, connectivity modeling, or retail health assessment. A robust urban metrics system will provide standardized calculations for POI and transit accessibility within 15-minute walk/bike sheds, intersection density analysis, bikeway network connectivity, retail health indicators (vacancy rates and rent trends), and daytime population dynamics - enabling consistent urban convenience scoring and comparative analysis across all US markets.

## What Changes

- **ADD** `aker_core.urban.poi_counts()` function for counting POIs and transit stops within 15-minute isochrones
- **ADD** `aker_core.urban.rent_trend()` function for analyzing retail rent trends and vacancy patterns
- **ADD** comprehensive urban connectivity analysis including intersection density and bikeway network assessment
- **ADD** daytime population calculation and enrichment for 1-mile buffers
- **ADD** standardized 15-minute accessibility modeling with walk (4.8 km/h) and bike (15 km/h) speed assumptions
- **ADD** database schema for `market_urban` table with all urban convenience metrics and metadata
- **ADD** data integration with OSM POIs, GTFS transit feeds, and local retail datasets
- **ADD** comprehensive validation framework ensuring count reproducibility on fixed POI datasets
- **ADD** performance optimizations for large-scale urban analysis across all US MSAs
- **ADD** integration with lifestyle scoring for comprehensive urban convenience assessment
- **BREAKING**: None - new capability extending urban analysis without disrupting existing functionality

## Impact

- **Affected specs**: Urban analysis capability, database schema, lifestyle scoring integration
- **Affected code**: `src/aker_core/urban/`, `src/aker_core/database/`, `src/aker_core/scoring/`, `tests/core/test_urban_metrics.py`, environmental data pipelines
- **Dependencies**: Geospatial libraries (GeoPandas, Shapely, NetworkX), transit data (GTFS), POI data (OSM), time series analysis (pandas, numpy)
- **Risk**: Medium - urban accessibility modeling requires accurate isochrone generation and POI classification
- **Performance**: Optimized for batch processing of urban metrics with efficient spatial operations
- **Scalability**: Designed to handle all US MSAs with spatial indexing and incremental updates
