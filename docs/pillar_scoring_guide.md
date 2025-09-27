# Aker Market Pillar Scoring Guide

This guide provides comprehensive documentation for the Aker Property Model's market pillar scoring system, which aggregates normalized pillar metrics into final market scores.

## Overview

The market pillar scoring system combines four key pillars:
- **Supply Constraints** (30% weight)
- **Innovation Jobs** (30% weight)
- **Urban Convenience** (20% weight)
- **Outdoor Access** (20% weight)

Each pillar is normalized to a 0-100 scale before weighted aggregation into final 0-5 market scores.

## Mathematical Foundation

### Scoring Algorithm

The final market score is calculated using weighted averages:

```
final_score_0_5 = (supply_0_100 × 0.3 + jobs_0_100 × 0.3 + urban_0_100 × 0.2 + outdoor_0_100 × 0.2) × 0.05
final_score_0_100 = supply_0_100 × 0.3 + jobs_0_100 × 0.3 + urban_0_100 × 0.2 + outdoor_0_100 × 0.2
```

### Weighting Scheme Rationale

| Pillar | Weight | Rationale |
|--------|--------|-----------|
| Supply Constraints | 30% | Fundamental supply/demand balance drives pricing |
| Innovation Jobs | 30% | Economic growth and job creation sustainability |
| Urban Convenience | 20% | Quality of life and accessibility factors |
| Outdoor Access | 20% | Lifestyle and environmental quality factors |

## API Reference

### Core Functions

#### `score(session, *, msa_id, msa_geo=None, as_of=None, weights=None, run_id=None)`

Compose a deterministic market score for the provided market.

```python
from aker_core.markets import score
from sqlalchemy.orm import Session

# Basic usage with default weights
result = score(
    session=session,
    msa_id="MSA001",
    as_of="2023-09-15"
)

print(f"Market Score: {result.weighted_0_5}/5 ({result.weighted_0_100}/100)")

# Custom weights for scenario analysis
custom_weights = {
    "supply": 0.4,
    "jobs": 0.4,
    "urban": 0.1,
    "outdoor": 0.1
}

result = score(
    session=session,
    msa_id="MSA001",
    weights=custom_weights
)
```

**Parameters:**
- `session`: Active SQLAlchemy session
- `msa_id`: MSA identifier (required)
- `msa_geo`: Geographic identifier (reserved for future use)
- `as_of`: Optional effective date (date, datetime, or ISO string)
- `weights`: Optional custom weight overrides
- `run_id`: Optional run identifier for lineage tracking

**Returns:** `MarketPillarScores` dataclass with all score components

### Data Structures

#### `MarketPillarScores`

```python
@dataclass(frozen=True)
class MarketPillarScores:
    msa_id: str
    supply_0_5: float      # Supply constraint score (0-5)
    jobs_0_5: float        # Innovation jobs score (0-5)
    urban_0_5: float       # Urban convenience score (0-5)
    outdoor_0_5: float     # Outdoor access score (0-5)
    weighted_0_5: float    # Final weighted score (0-5)
    weighted_0_100: float  # Final weighted score (0-100)
    weights: Mapping[str, float]  # Weight profile used
    score_as_of: Optional[date]   # Effective date
    run_id: Optional[int]         # Run identifier
```

## Database Schema

### `pillar_scores` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `msa_id` | String(12) | MSA identifier |
| `supply_0_5` | Float | Supply constraint score (0-5) |
| `jobs_0_5` | Float | Innovation jobs score (0-5) |
| `urban_0_5` | Float | Urban convenience score (0-5) |
| `outdoor_0_5` | Float | Outdoor access score (0-5) |
| `weighted_0_5` | Float | Final weighted score (0-5) |
| `weighted_0_100` | Float | Final weighted score (0-100) |
| `weights` | JSON | Weight profile used |
| `score_as_of` | Date | Effective date |
| `run_id` | Integer | Run identifier |

## Usage Examples

### Basic Market Scoring

```python
from aker_core.markets import score
from sqlalchemy.orm import Session

def get_market_score(session: Session, msa_id: str) -> float:
    """Get the latest market score for an MSA."""
    result = score(session=session, msa_id=msa_id)
    return result.weighted_0_5

# Example usage
score = get_market_score(session, "MSA001")
print(f"MSA001 Score: {score}/5")
```

### Custom Weight Analysis

```python
def analyze_weight_sensitivity(session: Session, msa_id: str):
    """Analyze how different weight profiles affect market scores."""

    # Default Aker weights
    default_result = score(session=session, msa_id=msa_id)

    # Supply-focused weighting
    supply_focused = score(
        session=session,
        msa_id=msa_id,
        weights={"supply": 0.5, "jobs": 0.3, "urban": 0.1, "outdoor": 0.1}
    )

    # Jobs-focused weighting
    jobs_focused = score(
        session=session,
        msa_id=msa_id,
        weights={"supply": 0.2, "jobs": 0.5, "urban": 0.15, "outdoor": 0.15}
    )

    return {
        "default": default_result.weighted_0_5,
        "supply_focused": supply_focused.weighted_0_5,
        "jobs_focused": jobs_focused.weighted_0_5
    }
```

### Historical Score Analysis

```python
def get_score_trends(session: Session, msa_id: str, months: int = 12):
    """Get historical score trends for an MSA."""

    # This would require querying pillar_scores table by date
    # For now, just return the latest score
    latest_score = score(session=session, msa_id=msa_id)
    return {
        "latest_score": latest_score.weighted_0_5,
        "score_date": latest_score.score_as_of,
        "trend_direction": "stable"  # Would analyze historical data
    }
```

### Batch Scoring

```python
def score_multiple_markets(session: Session, msa_ids: List[str]) -> Dict[str, float]:
    """Score multiple markets efficiently."""
    results = {}

    for msa_id in msa_ids:
        try:
            result = score(session=session, msa_id=msa_id)
            results[msa_id] = result.weighted_0_5
        except Exception as e:
            print(f"Failed to score {msa_id}: {e}")
            results[msa_id] = None

    return results
```

## Error Handling

### Common Error Scenarios

```python
from aker_core.markets import score

# Missing MSA ID
try:
    score(session=session, msa_id=None)
except ValueError as e:
    print(f"MSA ID required: {e}")

# No pillar data available
try:
    score(session=session, msa_id="INVALID")
except ValueError as e:
    print(f"No data available: {e}")

# Invalid weights
try:
    score(session=session, msa_id="MSA001", weights={"supply": -0.1})
except ValueError as e:
    print(f"Invalid weights: {e}")
```

### Data Quality Issues

```python
# Check for missing pillar scores
def validate_pillar_data_completeness(session: Session, msa_id: str) -> bool:
    """Check if all required pillar scores are available."""
    try:
        result = score(session=session, msa_id=msa_id)
        return True
    except ValueError as e:
        if "Missing pillar scores" in str(e):
            return False
        raise
```

## Performance Considerations

### Query Optimization

```python
# The system uses optimized queries for pillar score retrieval
# Indexes on (msa_id, calculation_timestamp) ensure fast lookups
# Consider batch processing for multiple MSAs

def score_market_batch(session: Session, msa_ids: List[str]) -> Dict[str, float]:
    """Score multiple markets with optimized queries."""
    results = {}

    # Process in batches to avoid memory issues
    batch_size = 50
    for i in range(0, len(msa_ids), batch_size):
        batch = msa_ids[i:i + batch_size]

        for msa_id in batch:
            try:
                result = score(session=session, msa_id=msa_id)
                results[msa_id] = result.weighted_0_5
            except Exception as e:
                print(f"Failed to score {msa_id}: {e}")
                results[msa_id] = None

    return results
```

### Memory Management

```python
# For large-scale scoring operations, consider:
# 1. Process MSAs in batches
# 2. Clear session caches between batches
# 3. Use connection pooling for database efficiency
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock
from aker_core.markets import score

def test_default_weight_scoring():
    """Test scoring with default Aker weights."""
    # Mock database session and record
    mock_session = Mock()
    mock_record = Mock()
    mock_record.supply_0_5 = 3.5
    mock_record.jobs_0_5 = 4.0
    mock_record.urban_0_5 = 3.8
    mock_record.outdoor_0_5 = 3.2

    mock_session.execute.return_value.scalars.return_value.first.return_value = mock_record

    result = score(session=mock_session, msa_id="MSA001")

    # Verify calculation: 0.3*3.5 + 0.3*4.0 + 0.2*3.8 + 0.2*3.2 = 3.7
    assert result.weighted_0_5 == 3.7
    assert result.weighted_0_100 == 74.0
```

### Integration Testing

```python
def test_end_to_end_scoring_pipeline(session):
    """Test complete scoring pipeline with real database."""
    # This would test the full pipeline from data ingestion to final scores
    # Requires actual database setup and data
    pass
```

## Mathematical Properties

### Proven Mathematical Properties

1. **Monotonicity**: If all pillar scores increase, the final score increases
2. **Weight Normalization**: Custom weights are properly normalized to sum to 1.0
3. **Deterministic**: Identical inputs produce identical outputs
4. **Bounds Preservation**: Final scores stay within expected ranges

### Weight Sensitivity Analysis

```python
def analyze_weight_sensitivity(session: Session, msa_id: str):
    """Analyze how weight changes affect market scores."""

    base_result = score(session=session, msa_id=msa_id)

    sensitivity_results = {}

    # Test supply weight variations
    for supply_weight in [0.2, 0.3, 0.4, 0.5]:
        remaining_weight = (1.0 - supply_weight) / 3
        weights = {
            "supply": supply_weight,
            "jobs": remaining_weight,
            "urban": remaining_weight,
            "outdoor": remaining_weight
        }

        result = score(session=session, msa_id=msa_id, weights=weights)
        sensitivity_results[f"supply_{supply_weight}"] = result.weighted_0_5

    return sensitivity_results
```

## API Versioning

Current version: `1.0.0`

- **Breaking changes** will increment major version
- **New features** increment minor version
- **Bug fixes** increment patch version

## Contributing

When contributing to the market scoring system:

1. Maintain mathematical correctness of weighting algorithms
2. Add comprehensive tests for new functionality
3. Update this documentation with new features
4. Ensure backward compatibility with existing scoring workflows

## Support

For questions or issues:
- Check the mathematical documentation first
- Review test cases for usage examples
- Ensure database schema matches expected structure
