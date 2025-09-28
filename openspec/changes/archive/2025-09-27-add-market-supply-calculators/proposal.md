## Why

The Aker Property Model requires standardized supply constraint calculators to transform raw market data into normalized 0-100 scores for the Supply pillar. Currently, supply constraint scoring relies on ad-hoc metric calculations without proper standardization, making it difficult to benchmark markets consistently or audit how elasticity proxies, vacancy rates, and lease-up time-on-market feed into the final `market_supply` scores. Standardized calculators with comprehensive validation will ensure consistent, auditable supply constraint scoring across all markets.

## What Changes

- **ADD** `aker_core.supply.elasticity()` function for calculating 3-year average building permits per 1,000 households (inverse scoring)
- **ADD** `aker_core.supply.vacancy()` function for processing HUD vacancy data with proper normalization
- **ADD** `aker_core.supply.leaseup_tom()` function for calculating multi-family lease-up time-on-market metrics
- **ADD** comprehensive input validation and error handling for all calculators
- **ADD** Great Expectations data validation suites for supply metrics with range and reasonableness checks
- **ADD** integration layer for feeding calculator outputs into `market_supply` table with inverse scoring logic
- **ADD** comprehensive test suite with unit tests, property tests, and golden-master validation
- **ADD** performance optimizations for large-scale market processing
- **BREAKING**: None - new calculators complement existing supply analysis

## Impact

- **Affected specs**: Core supply analysis functionality, database schema
- **Affected code**: `src/aker_core/supply/`, `src/aker_core/database/`, `tests/core/test_supply_calculators.py`, Great Expectations suites
- **Dependencies**: NumPy/Pandas for calculations, SQLAlchemy for database integration, Great Expectations for data validation
- **Risk**: Medium - new calculation methods require thorough validation against existing benchmarks
- **Performance**: Optimized for batch processing of multiple markets with vectorized operations
- **Scalability**: Designed to handle all US MSAs with efficient database operations
