# Aker Supply Calculators Guide

This guide provides comprehensive documentation for the Aker Property Model's supply constraint calculators, which implement the mathematical foundation for the Supply pillar of the Aker scoring system.

## Overview

The supply constraint calculators transform raw market data into normalized metrics that measure supply constraints across US markets. The calculators implement three key metrics:

1. **Elasticity**: Building permits per 1,000 households (inverse supply constraint proxy)
2. **Vacancy**: Rental vacancy rates (inverse supply constraint proxy)
3. **Lease-Up Time**: Multi-family lease-up time-on-market (inverse supply constraint proxy)

## Mathematical Foundation

### Elasticity Calculation

**Formula:**
```
elasticity = (permits / households) × 1000
```

Where:
- `permits`: Annual building permit counts
- `households`: Annual household counts
- Returns: Permits per 1,000 households (higher = more supply-responsive)

**Inverse Scoring Logic:**
```
constraint_score = 100 - (elasticity / max_elasticity) × 100
```

### Vacancy Rate Calculation

**Formula:**
```
vacancy_rate = average(hud_vacancy_data)
```

**Inverse Scoring Logic:**
```
constraint_score = 100 - vacancy_rate
```

### Lease-Up Time Calculation

**Formula:**
```
leaseup_days = median(days_on_market)
```

**Inverse Scoring Logic:**
```
constraint_score = 100 - (leaseup_days / 90) × 100
```

## API Reference

### Core Functions

#### `elasticity(permits, households, years=3)`

Calculates building permit elasticity as permits per 1,000 households.

```python
from aker_core.supply import elasticity

# Basic usage
permits = [1200, 1350, 1100, 1400]
households = [52000, 52500, 53000, 53500]
elasticity_value = elasticity(permits, households, years=3)
# Returns: 22.115 (permits per 1k households)

# With pandas
import pandas as pd
permits_series = pd.Series([1200, 1350, 1100, 1400])
households_series = pd.Series([52000, 52500, 53000, 53500])
elasticity_value = elasticity(permits_series, households_series)
```

**Parameters:**
- `permits`: Array-like of annual building permit counts
- `households`: Array-like of annual household counts
- `years`: Number of years to average (default: 3)

**Returns:** Float representing permits per 1,000 households

**Raises:**
- `ValueError`: If array lengths don't match or invalid inputs
- `ZeroDivisionError`: If households contain zero values

#### `vacancy(hud_data, msa_boundaries=None, vacancy_type="rental")`

Calculates rental vacancy rates from HUD data.

```python
from aker_core.supply import vacancy

# Basic usage
hud_data = {
    'year': [2020, 2021, 2022],
    'vacancy_rate': [5.2, 4.8, 4.5],
    'geography': ['MSA001', 'MSA001', 'MSA001']
}
vacancy_rate = vacancy(hud_data)
# Returns: 4.833 (%)

# With DataFrame
import pandas as pd
df = pd.DataFrame(hud_data)
vacancy_rate = vacancy(df, vacancy_type='multifamily')
```

**Parameters:**
- `hud_data`: Dictionary or DataFrame with HUD vacancy data
- `msa_boundaries`: Optional geographic boundaries for aggregation
- `vacancy_type`: Type of vacancy ('rental', 'multifamily', 'overall')

**Returns:** Float representing vacancy rate as percentage

#### `leaseup_tom(lease_data, property_filters=None, time_window_days=90)`

Calculates multi-family lease-up time-on-market.

```python
from aker_core.supply import leaseup_tom
import pandas as pd

# Basic usage
lease_data = {
    'lease_date': pd.date_range('2023-01-01', periods=50, freq='D'),
    'property_id': ['PROP001'] * 25 + ['PROP002'] * 25,
    'days_on_market': [15, 20, 25, 18, 22] * 10
}
leaseup_days = leaseup_tom(lease_data)
# Returns: 20.0 (median days)

# With property filtering
filtered_leaseup = leaseup_tom(
    lease_data,
    property_filters={'property_type': 'apartment'}
)
```

**Parameters:**
- `lease_data`: Dictionary or DataFrame with lease transaction data
- `property_filters`: Optional filters for property characteristics
- `time_window_days`: Analysis window in days (default: 90)

**Returns:** Float representing median days on market

### Integration Functions

#### `calculate_supply_metrics(session, msa_id, permits_data, households_data, hud_vacancy_data, lease_data, data_vintage, **kwargs)`

High-level function for calculating and persisting all supply metrics.

```python
from aker_core.supply import calculate_supply_metrics
from sqlalchemy.orm import Session

# Calculate and persist all metrics
result = calculate_supply_metrics(
    session=session,
    msa_id="MSA001",
    permits_data=[1200, 1350, 1100, 1400],
    households_data=[52000, 52500, 53000, 53500],
    hud_vacancy_data=hud_data_dict,
    lease_data=lease_data_dict,
    data_vintage="2023-09-15",
    run_id=12345
)

print(f"Record ID: {result['record_id']}")
print(f"Elasticity: {result['elasticity']:.2f}")
print(f"Vacancy: {result['vacancy']:.2f}")
print(f"Lease-up: {result['leaseup_days']:.1f}")
```

#### `get_supply_scores_for_scoring(session, msa_id, as_of=None)`

Get supply constraint scores formatted for pillar scoring pipeline.

```python
from aker_core.supply import get_supply_scores_for_scoring

scores = get_supply_scores_for_scoring(session, "MSA001")
print(f"Elasticity Score: {scores['elasticity_score']:.1f}")
print(f"Vacancy Score: {scores['vacancy_score']:.1f}")
print(f"Lease-Up Score: {scores['leaseup_score']:.1f}")
print(f"Composite Score: {scores['composite_supply_score']:.1f}")
```

#### `validate_supply_data_quality(session, msa_ids=None)`

Validate supply metrics data quality using Great Expectations.

```python
from aker_core.supply import validate_supply_data_quality

quality = validate_supply_data_quality(session)
print(f"Total Records: {quality['summary_stats']['total_records']}")
print(f"Overall Quality: {quality['overall_quality']}")
```

## Data Requirements

### Elasticity Data
- **Source**: Local building permit portals, Census Bureau
- **Format**: Annual permit counts and household estimates
- **Geographic**: MSA-level aggregation
- **Temporal**: 3+ years of historical data

### Vacancy Data
- **Source**: HUD, local housing authorities
- **Format**: Annual vacancy rates by geography
- **Types**: Rental, multi-family, overall
- **Validation**: 0-100% range, data completeness

### Lease-Up Data
- **Source**: Property management systems, lease transaction databases
- **Format**: Individual lease records with dates and property info
- **Filters**: Multi-family properties, recent time window
- **Quality**: Sufficient sample size for statistical reliability

## Integration Examples

### ETL Pipeline Integration

```python
from aker_core.supply import calculate_supply_metrics
from sqlalchemy.orm import Session

def process_supply_data(session: Session, msa_data: dict):
    """Process supply data for an MSA and store results."""

    # Extract data from various sources
    permits = msa_data['building_permits']  # List of annual counts
    households = msa_data['household_estimates']  # List of annual counts
    hud_data = msa_data['hud_vacancy']  # Dict with HUD data
    lease_data = msa_data['lease_transactions']  # Dict with lease data

    # Calculate and persist metrics
    result = calculate_supply_metrics(
        session=session,
        msa_id=msa_data['msa_id'],
        permits_data=permits,
        households_data=households,
        hud_vacancy_data=hud_data,
        lease_data=lease_data,
        data_vintage=msa_data['data_vintage'],
        run_id=msa_data['run_id']
    )

    return result
```

### Scoring Pipeline Integration

```python
from aker_core.supply import get_supply_scores_for_scoring
from aker_core.markets.composer import score

def calculate_market_score(session: Session, msa_id: str):
    """Calculate complete market score including supply pillar."""

    # Get supply constraint scores
    supply_scores = get_supply_scores_for_scoring(session, msa_id)

    # Get other pillar scores (placeholder - would come from other calculators)
    jobs_score = 75.0  # Placeholder
    urban_score = 80.0  # Placeholder
    outdoor_score = 70.0  # Placeholder

    # Calculate final market score using Aker weights
    final_score = score(
        session=session,
        msa_id=msa_id,
        supply_0_5=supply_scores['composite_supply_score'] / 20,  # Convert 0-100 to 0-5
        jobs_0_5=jobs_score / 20,
        urban_0_5=urban_score / 20,
        outdoor_0_5=outdoor_score / 20
    )

    return final_score
```

## Error Handling

### Common Error Patterns

```python
from aker_core.supply import elasticity, vacancy, leaseup_tom

# Handle insufficient data
try:
    elasticity([1000], [50000], years=3)  # Need at least 3 years
except ValueError as e:
    print(f"Insufficient data: {e}")

# Handle invalid vacancy rates
try:
    vacancy({'year': [2020], 'vacancy_rate': [-5.0]})  # Negative rate
except ValueError as e:
    print(f"Invalid vacancy rate: {e}")

# Handle missing lease data
try:
    leaseup_tom({'lease_date': [], 'days_on_market': []})
except ValueError as e:
    print(f"Insufficient lease data: {e}")
```

### Data Quality Issues

```python
# Check for data completeness
quality = validate_supply_data_quality(session)
if not quality['overall_quality']:
    print("Data quality issues detected:")
    for check, passed in quality['quality_checks'].items():
        if not passed:
            print(f"  - {check}: FAILED")
```

## Performance Considerations

### Large Dataset Optimization

```python
import numpy as np
from aker_core.supply import elasticity

# For large datasets, use numpy arrays for better performance
permits_array = np.array([1200, 1350, 1100, 1400])
households_array = np.array([52000, 52500, 53000, 53500])

# Vectorized operations are automatically used
elasticity_value = elasticity(permits_array, households_array)
```

### Memory Management

```python
# For memory-constrained environments, process data in chunks
def process_large_dataset_in_chunks(data, chunk_size=1000):
    results = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        result = elasticity(chunk['permits'], chunk['households'])
        results.append(result)
    return results
```

## Testing and Validation

### Unit Testing

```python
import pytest
from aker_core.supply import elasticity

def test_elasticity_calculation():
    """Test basic elasticity calculation."""
    permits = [1000, 1100, 1200]
    households = [50000, 51000, 52000]

    result = elasticity(permits, households)
    expected = 22.115  # (1000/50000 + 1100/51000 + 1200/52000) / 3 * 1000

    assert abs(result - expected) < 0.001

def test_elasticity_error_handling():
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        elasticity([1000], [50000], years=3)  # Insufficient data

    with pytest.raises(ZeroDivisionError):
        elasticity([1000, 1100, 1200], [50000, 0, 52000])  # Zero households
```

### Integration Testing

```python
def test_supply_calculator_integration(session):
    """Test integration of all supply calculators."""

    # Mock data for testing
    msa_id = "TEST001"
    permits_data = [1200, 1350, 1100, 1400]
    households_data = [52000, 52500, 53000, 53500]
    hud_data = {
        'year': [2020, 2021, 2022],
        'vacancy_rate': [5.2, 4.8, 4.5],
        'geography': ['TEST001'] * 3
    }
    lease_data = {
        'lease_date': pd.date_range('2023-01-01', periods=30, freq='D'),
        'days_on_market': [15, 20, 25] * 10
    }

    # Calculate and persist
    result = calculate_supply_metrics(
        session=session,
        msa_id=msa_id,
        permits_data=permits_data,
        households_data=households_data,
        hud_vacancy_data=hud_data,
        lease_data=lease_data,
        data_vintage="2023-09-15"
    )

    assert result['elasticity'] > 0
    assert result['vacancy'] > 0
    assert result['leaseup_days'] > 0
    assert result['record_id'] is not None
```

## Troubleshooting

### Common Issues

**"Insufficient data" errors:**
- Ensure you have at least 3 years of permit/household data for elasticity
- Check that vacancy data spans multiple years
- Verify lease data has recent transactions (within time window)

**Data format issues:**
- Ensure arrays/lists have matching lengths
- Check that vacancy rates are percentages (0-100)
- Validate date formats are ISO strings or datetime objects

**Performance problems:**
- Use numpy arrays instead of lists for large datasets
- Process data in chunks for very large datasets
- Consider caching frequently accessed calculations

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Supply calculators will log detailed information
elasticity_value = elasticity(permits, households)
```

## API Versioning

Current version: `1.0.0`

- **Breaking changes** will increment major version
- **New features** increment minor version
- **Bug fixes** increment patch version

## Contributing

When contributing to the supply calculators:

1. Add comprehensive tests for new functionality
2. Update mathematical documentation
3. Ensure backward compatibility
4. Update this guide with new features

## Support

For questions or issues:
- Check the mathematical documentation first
- Review test cases for usage examples
- Ensure data format matches expected inputs
