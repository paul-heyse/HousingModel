## Why

The Aker Property Model requires a robust pillar aggregation and 0-5 bucketing system to transform normalized 0-100 pillar scores into final 0-5 market scores. This implements the core scoring algorithm that produces the standardized market fit scores used throughout the investment decision pipeline. The system must handle the official Aker weighting scheme (Supply 30%, Jobs 30%, Urban 20%, Outdoors 20%) while providing flexibility for custom weightings, comprehensive error handling, and full auditability through database persistence with run context tracking.

## What Changes

- **ADD** `scoring.pillar_score()` function implementing weighted mean aggregation with comprehensive input validation
- **ADD** `scoring.to_five_bucket()` function implementing quantile-based 0-5 mapping with configurable boundaries
- **ADD** database persistence layer for `pillar_scores` table with run_id, risk_multiplier, and metadata tracking
- **ADD** risk multiplier integration for adjusting final scores based on market-specific peril assessments
- **ADD** comprehensive test suite including golden-master tests, property-based testing, and integration tests
- **ADD** performance optimizations for large-scale market scoring operations
- **BREAKING**: None - implements existing mathematical specification without changing current behavior

## Impact

- **Affected specs**: Core scoring functionality, database schema
- **Affected code**: `src/aker_core/scoring.py`, `src/aker_core/database/`, `tests/core/test_pillar_scoring.py`
- **Dependencies**: NumPy for mathematical operations, SQLAlchemy for database integration, pytest for testing framework
- **Risk**: Low - implements well-defined mathematical operations with comprehensive validation
- **Performance**: Optimized for batch processing of multiple markets with vectorized operations
- **Scalability**: Designed to handle scoring for all US MSAs with efficient database queries
