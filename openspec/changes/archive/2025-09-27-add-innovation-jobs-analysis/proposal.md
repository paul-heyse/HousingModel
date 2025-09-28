## Why

The Aker Property Model requires comprehensive innovation jobs and human capital analysis to evaluate market employment dynamics. This includes calculating location quotients for targeted NAICS sectors, 3-year compound annual growth rates, tracking major expansions, research funding awards, business formation statistics, and demographic migration patterns - all critical indicators of innovation-driven economic growth.

## What Changes

- **ADD** location quotient calculation for targeted NAICS sectors
- **ADD** 3-year CAGR calculation for employment time series
- **ADD** expansion tracking for universities, health, semis, and defense sectors
- **ADD** NIH/NSF/DoD awards analysis per 100k population
- **ADD** business formation statistics integration
- **ADD** net migration analysis for 25-44 age group
- **ADD** database schema for `market_jobs` table with normalized metrics
- **BREAKING**: None - new capability extending market analysis

## Impact

- **Affected specs**: New jobs analysis capability
- **Affected code**: `src/aker_jobs/`, database schema, ETL pipelines
- **Dependencies**: BLS data, BEA data, Census migration data, NIH/NSF/DoD APIs
- **Risk**: Medium - new data sources and calculation methods require validation
