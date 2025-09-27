## Why

The Aker Property Model requires comprehensive outdoor recreation and environmental quality analysis to evaluate market livability and outdoor lifestyle factors. Currently, outdoor access scoring relies on basic proximity metrics without considering air quality dynamics, noise pollution, wildfire smoke impacts, or comprehensive trail network analysis. A robust environmental analysis system will provide detailed assessments of air quality variation, smoke exposure risk, noise pollution from transportation infrastructure, and comprehensive outdoor recreation accessibility - enabling more accurate lifestyle scoring and health risk assessment for investment decisions.

## What Changes

- **ADD** `aker_outdoors.air.pm25_variation()` function for calculating PM2.5 air quality seasonal and temporal variation
- **ADD** `aker_outdoors.smoke.rolling_days()` function for tracking wildfire smoke exposure over rolling time windows
- **ADD** `aker_outdoors.noise.highway_proximity()` function for assessing transportation noise pollution impact
- **ADD** comprehensive outdoor recreation accessibility analysis including trail networks, park systems, and water body access
- **ADD** environmental risk scoring integration with health and lifestyle factors
- **ADD** database schema for `market_outdoors` table with environmental and recreation metrics
- **ADD** data integration with EPA AirNow, NOAA HMS smoke data, OSM trail networks, and transportation noise modeling
- **ADD** comprehensive validation against environmental monitoring feeds and ground truth data
- **ADD** performance optimizations for large-scale geospatial environmental analysis
- **ADD** integration with lifestyle scoring for comprehensive outdoor livability assessment
- **BREAKING**: None - new capability extending environmental analysis without disrupting existing functionality

## Impact

- **Affected specs**: Environmental analysis capability, outdoor recreation assessment, database schema
- **Affected code**: `src/aker_outdoors/`, `src/aker_core/database/`, `src/aker_geo/`, `tests/outdoors/`, environmental data pipelines
- **Dependencies**: Geospatial libraries (GeoPandas, Shapely), environmental APIs (EPA AirNow, NOAA), noise modeling libraries, time series analysis (pandas, numpy)
- **Risk**: Medium - environmental data quality and geospatial analysis accuracy require careful validation
- **Performance**: Optimized for batch processing of environmental time series and geospatial calculations
- **Scalability**: Designed to handle all US MSAs with efficient spatial indexing and time series processing
