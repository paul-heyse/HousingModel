## Why

The Aker Property Model requires robust data normalization to transform raw market metrics into standardized 0-100 scores for consistent comparison across different markets and time periods. All pillar metrics (Supply Constraints, Innovation Jobs, Urban Convenience, Outdoor Access) must be normalized to a common scale before aggregation into final market scores. The current project specification references a `robust_minmax` function but lacks a dedicated, thoroughly tested implementation with comprehensive property-based test coverage and production-ready error handling.

## What Changes

- **ADD** `scoring.robust_minmax()` function implementing winsorized robust min-max normalization
- **ADD** comprehensive property-based tests ensuring mathematical correctness (monotonicity, scaling invariance, bounds)
- **ADD** robust error handling for edge cases (empty arrays, all NaN values, invalid parameters)
- **ADD** configurable percentile parameters for different robustness requirements
- **ADD** performance optimizations for large-scale market data processing
- **ADD** integration with the complete scoring pipeline from raw metrics to final scores
- **ADD** comprehensive documentation with mathematical proofs and usage examples
- **ADD** validation against existing project specification in project.md
- **ADD** cross-platform compatibility and numerical stability guarantees
- **BREAKING**: None - this implements existing mathematical specification without changing current behavior

## Impact

- **Affected specs**: Core scoring functionality, pillar normalization, mathematical foundations
- **Affected code**: `src/aker_core/scoring.py`, `tests/core/test_normalization.py`, scoring pipeline integration
- **Dependencies**: NumPy for array operations, pytest for property testing, Hypothesis for property-based testing
- **Risk**: Low - implements well-defined mathematical operations with comprehensive validation
- **Performance**: Optimized for vectorized operations on large market datasets with minimal memory overhead
- **Scalability**: Designed to handle normalization for all US MSAs with consistent performance
