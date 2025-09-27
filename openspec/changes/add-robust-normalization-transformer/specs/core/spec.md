## ADDED Requirements

### Requirement: Robust Normalization Mathematical Foundation
The system SHALL provide a `robust_minmax()` function in `aker_core.scoring` that implements winsorized robust min-max normalization with mathematically proven properties for transforming raw market metrics to standardized 0-100 scores.

#### Scenario: Winsorized Robust Min-Max Algorithm
- **GIVEN** an array of raw metric values with potential outliers
- **WHEN** `scoring.robust_minmax(array, p_low=0.05, p_high=0.95)` is called
- **THEN** the function SHALL calculate the 5th and 95th percentiles as robust bounds
- **AND** apply winsorization by clipping values outside these bounds
- **AND** perform min-max normalization: `100 * (x - min_bound) / (max_bound - min_bound)`
- **AND** return a numpy array with values in the range [0, 100]

#### Scenario: Monotonicity Preservation (Mathematical Property)
- **GIVEN** any two input arrays where `x[i] ≤ y[i]` for all indices i
- **WHEN** both arrays are normalized using `robust_minmax()` with identical parameters
- **THEN** the normalized values SHALL maintain the same order: `result_x[i] ≤ result_y[i]` for all i
- **AND** this property SHALL hold regardless of the percentile parameters chosen
- **AND** the monotonicity SHALL be preserved even with extreme outliers in the data

#### Scenario: Scaling Invariance (Mathematical Property)
- **GIVEN** an input array and the same array scaled by a positive constant factor c > 0
- **WHEN** both arrays are normalized using `robust_minmax()` with identical parameters
- **THEN** the normalized results SHALL be identical within numerical precision
- **AND** the scaling factor SHALL not affect the relative ordering of normalized values
- **AND** this property SHALL hold for any positive scaling factor

#### Scenario: Bounds Guarantee (Mathematical Property)
- **GIVEN** any valid input array (non-empty, contains at least one finite numeric value)
- **WHEN** the array is normalized using `robust_minmax()`
- **THEN** all output values SHALL be in the closed interval [0, 100]
- **AND** the minimum output value SHALL be ≥ 0
- **AND** the maximum output value SHALL be ≤ 100
- **AND** this guarantee SHALL hold for all valid percentile parameter combinations

#### Scenario: Configurable Percentile Parameters
- **GIVEN** different robustness requirements for outlier handling
- **WHEN** `robust_minmax()` is called with custom percentile parameters
- **THEN** the function SHALL accept `p_low` and `p_high` parameters in range [0, 1]
- **AND** validate that `p_low < p_high` with appropriate error messages
- **AND** use default values of `p_low=0.05` and `p_high=0.95` when not specified
- **AND** support different robustness levels for different market characteristics

#### Scenario: Comprehensive Input Validation
- **GIVEN** various types of input data and parameters
- **WHEN** `robust_minmax()` is called
- **THEN** the function SHALL validate that input is a numpy array or array-like
- **AND** check that percentile parameters are valid floats in [0, 1] range
- **AND** ensure `p_low < p_high` with clear error messages
- **AND** handle edge cases gracefully with informative error messages

#### Scenario: Edge Case Handling and Robustness
- **GIVEN** arrays with extreme characteristics (empty, all NaN, single values, constant values)
- **WHEN** `robust_minmax()` processes these arrays
- **THEN** the function SHALL handle empty arrays with appropriate ValueError
- **AND** handle arrays with all NaN values with informative error messages
- **AND** handle single-value arrays by returning appropriate normalized results
- **AND** handle constant arrays by returning the midpoint (50.0) value

#### Scenario: Numerical Stability and Precision
- **GIVEN** arrays with extreme value ranges or precision requirements
- **WHEN** `robust_minmax()` performs calculations
- **THEN** the function SHALL maintain numerical stability across different value ranges
- **AND** use appropriate floating-point precision for financial calculations
- **AND** handle very small differences between min and max bounds
- **AND** provide consistent results across different computing platforms

#### Scenario: Performance Optimization for Large Datasets
- **GIVEN** large arrays representing market data for multiple MSAs
- **WHEN** `robust_minmax()` processes these arrays
- **THEN** the function SHALL use vectorized NumPy operations for efficiency
- **AND** minimize memory allocations and copies
- **AND** support batch processing of multiple arrays
- **AND** maintain performance characteristics suitable for real-time scoring

#### Scenario: Integration with Scoring Pipeline
- **GIVEN** normalized output from `robust_minmax()` and pillar aggregation functions
- **WHEN** the normalized values are used in the scoring pipeline
- **THEN** the normalized values SHALL be directly compatible with `pillar_score()` functions
- **AND** support both individual array normalization and batch processing
- **AND** integrate seamlessly with the complete scoring workflow from raw metrics to final scores

#### Scenario: Mathematical Correctness Validation
- **GIVEN** the mathematical properties and edge cases
- **WHEN** comprehensive testing is performed
- **THEN** all three core properties (monotonicity, scaling invariance, bounds) SHALL be validated
- **AND** edge cases SHALL be handled appropriately without violating mathematical guarantees
- **AND** numerical stability SHALL be maintained across different data distributions
- **AND** the implementation SHALL match the specification in project.md exactly

#### Scenario: Documentation and Mathematical Proofs
- **GIVEN** the need for mathematical rigor and developer understanding
- **WHEN** the function is documented and tested
- **THEN** the documentation SHALL include formal mathematical proofs of the three core properties
- **AND** provide clear explanations of the winsorization and normalization algorithms
- **AND** include usage examples demonstrating the mathematical properties
- **AND** provide guidance for selecting appropriate percentile parameters
