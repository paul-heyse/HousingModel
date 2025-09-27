# Aker Core Supply Module

The supply constraint calculators implement the mathematical foundation for the Supply pillar of the Aker Property Model scoring system.

## Overview

This module provides three key calculators for measuring supply constraints in US housing markets:

1. **Elasticity Calculator** - Measures building permit responsiveness to household growth
2. **Vacancy Calculator** - Analyzes rental vacancy rates as supply availability indicators
3. **Lease-Up Calculator** - Tracks multi-family lease-up time-on-market

## Quick Start

```python
from aker_core.supply import elasticity, vacancy, leaseup_tom

# Calculate elasticity (permits per 1k households)
permits = [1200, 1350, 1100, 1400]
households = [52000, 52500, 53000, 53500]
elasticity_value = elasticity(permits, households, years=3)

# Calculate vacancy rate
hud_data = {
    'year': [2020, 2021, 2022],
    'vacancy_rate': [5.2, 4.8, 4.5],
    'geography': ['MSA001', 'MSA001', 'MSA001']
}
vacancy_rate = vacancy(hud_data)

# Calculate lease-up time
lease_data = {
    'lease_date': pd.date_range('2023-01-01', periods=30, freq='D'),
    'days_on_market': [15, 20, 25] * 10
}
leaseup_days = leaseup_tom(lease_data)
```

## Mathematical Foundation

### Supply Constraint Theory

The Aker Property Model uses **inverse relationships** for supply constraint scoring:

- **Higher elasticity** (more permits per household) = **Lower constraint score**
- **Lower vacancy rates** = **Higher constraint score**
- **Shorter lease-up times** = **Higher constraint score**

### Scoring Logic

Each metric is normalized to 0-100 scale where:
- 0 = Very loose supply (unconstrained markets)
- 100 = Very tight supply (highly constrained markets)

## API Reference

### Core Functions

#### `elasticity(permits, households, years=3)`

Calculates building permit elasticity as permits per 1,000 households.

**Formula:**
```
elasticity = (permits / households) × 1000
```

**Parameters:**
- `permits`: Array of annual building permit counts
- `households`: Array of annual household counts
- `years`: Number of years to average (default: 3)

**Returns:** Float representing permits per 1,000 households

#### `vacancy(hud_data, msa_boundaries=None, vacancy_type="rental")`

Calculates rental vacancy rates from HUD data.

**Parameters:**
- `hud_data`: HUD vacancy data (DataFrame or dict)
- `msa_boundaries`: Optional geographic boundaries
- `vacancy_type`: Type of vacancy ('rental', 'multifamily', 'overall')

**Returns:** Float representing vacancy rate as percentage

#### `leaseup_tom(lease_data, property_filters=None, time_window_days=90)`

Calculates multi-family lease-up time-on-market.

**Parameters:**
- `lease_data`: Lease transaction data
- `property_filters`: Optional property type filters
- `time_window_days`: Analysis window in days (default: 90)

**Returns:** Float representing median days on market

### Integration Functions

#### `calculate_supply_metrics(session, msa_id, **kwargs)`

High-level function for calculating and persisting all supply metrics.

#### `get_supply_scores_for_scoring(session, msa_id, as_of=None)`

Get supply constraint scores formatted for pillar scoring pipeline.

#### `validate_supply_data_quality(session, msa_ids=None)`

Validate supply metrics data quality using Great Expectations.

## Data Sources

### Required Data

1. **Building Permits**: Annual permit counts from local building departments
2. **Household Estimates**: Annual household counts from Census Bureau
3. **HUD Vacancy Data**: Rental vacancy rates from HUD
4. **Lease Transaction Data**: Multi-family lease records with days on market

### Data Quality Requirements

- **Elasticity**: 3+ years of permit/household data
- **Vacancy**: Multi-year vacancy rate data
- **Lease-Up**: Recent lease transactions (within 90 days)

## Integration with Aker Ecosystem

### Pillar Scoring Integration

```python
from aker_core.supply import get_supply_scores_for_scoring
from aker_core.markets.composer import score

# Get supply scores (0-100 scale)
supply_scores = get_supply_scores_for_scoring(session, msa_id)

# Convert to 0-5 scale for pillar aggregation
supply_0_5 = supply_scores['composite_supply_score'] / 20

# Use in market scoring
final_score = score(
    session=session,
    msa_id=msa_id,
    supply_0_5=supply_0_5,
    # ... other pillar scores
)
```

### ETL Pipeline Integration

```python
from aker_core.supply import calculate_supply_metrics

# Process MSA data through supply calculators
result = calculate_supply_metrics(
    session=session,
    msa_id="MSA001",
    permits_data=permits_list,
    households_data=households_list,
    hud_vacancy_data=hud_dict,
    lease_data=lease_dict,
    data_vintage="2023-09-15"
)
```

## Testing

The module includes comprehensive test coverage:

```bash
# Run all supply calculator tests
pytest tests/core/test_supply_calculators.py -v

# Run specific test categories
pytest tests/core/test_supply_calculators.py::TestElasticityCalculator -v
pytest tests/core/test_supply_calculators.py::TestVacancyCalculator -v
pytest tests/core/test_supply_calculators.py::TestLeaseupCalculator -v
```

## Performance

- **Vectorized Operations**: NumPy-based implementation for efficiency
- **Memory Efficient**: Minimal memory allocations for large datasets
- **Batch Processing**: Support for processing multiple MSAs simultaneously
- **Caching**: Optional caching for frequently accessed calculations

## Error Handling

The calculators include comprehensive error handling:

- **Input Validation**: Array length matching, data type checking
- **Range Validation**: Vacancy rates (0-100%), days on market (0-365)
- **Edge Cases**: Zero households, negative permits, missing data
- **Graceful Degradation**: Informative error messages with diagnostic information

## Mathematical Validation

All calculators implement mathematically proven properties:

1. **Monotonicity**: Order-preserving transformations
2. **Scaling Invariance**: Results independent of scale factors
3. **Bounds Guarantee**: All outputs in expected ranges
4. **Numerical Stability**: Consistent results across platforms

## Version History

- **v1.0.0**: Initial implementation with core calculators
- **v1.1.0**: Added integration functions and database persistence
- **v1.2.0**: Enhanced error handling and validation
- **v1.3.0**: Performance optimizations and comprehensive testing

## Contributing

When contributing to the supply calculators:

1. Add tests for new functionality
2. Update mathematical documentation
3. Ensure backward compatibility
4. Update this README with new features

## License

Part of the Aker Property Model - see main project license.
