# Portfolio Exposure Monitoring

A comprehensive system for monitoring portfolio concentrations and generating alerts when exposure thresholds are breached.

## Overview

The portfolio exposure monitoring system provides real-time analysis of portfolio composition across multiple dimensions including strategy, geography, vintage, construction type, and rent bands. It automatically generates alerts when exposures exceed configured thresholds and provides dashboard-ready data for visualization.

## Core Features

- **Multi-dimensional exposure analysis** across strategy, state, MSA, vintage, construction type, and rent bands
- **Configurable threshold monitoring** with automatic alert generation
- **Real-time dashboard integration** with exposure dials and trend analysis
- **Geographic concentration analysis** for risk assessment
- **Import/export utilities** for portfolio positions and exposure data
- **Performance benchmarking** for large portfolios

## Quick Start

```python
from aker_portfolio import compute_exposures, PortfolioPosition

# Define portfolio positions
positions = [
    PortfolioPosition(
        asset_id="asset_1",
        strategy="value_add",
        state="CA",
        msa_id="31080",  # Los Angeles
        position_value=1000000,
        units=50
    ),
    PortfolioPosition(
        asset_id="asset_2",
        strategy="core_plus",
        state="TX",
        msa_id="19100",  # Dallas
        position_value=1500000,
        units=75
    )
]

# Compute exposures (requires database session)
result = compute_exposures(positions, db_session=your_db_session)

print(f"Total portfolio value: ${result.total_portfolio_value}")
print(f"Strategy exposures: {[(exp.dimension_value, exp.exposure_pct) for exp in result.exposures if exp.dimension_type == 'strategy']}")
```

## API Reference

### Core Functions

#### `compute_exposures(positions, as_of_date=None, include_alerts=True, db_session=None)`

Compute portfolio exposures across all dimensions.

**Parameters:**
- `positions`: List of `PortfolioPosition` objects
- `as_of_date`: Date for calculation (defaults to current date)
- `include_alerts`: Whether to check for threshold breaches
- `db_session`: Database session (required)

**Returns:** `ExposureResult` with calculated exposures

### Data Models

#### `PortfolioPosition`
```python
@dataclass
class PortfolioPosition:
    position_id: Optional[str] = None
    asset_id: Optional[str] = None
    msa_id: Optional[str] = None
    strategy: Optional[str] = None
    state: Optional[str] = None
    vintage: Optional[int] = None
    construction_type: Optional[str] = None
    rent_band: Optional[str] = None
    position_value: float
    units: Optional[int] = None
```

#### `ExposureResult`
```python
@dataclass
class ExposureResult:
    as_of_date: datetime
    total_portfolio_value: float
    exposures: list[ExposureDimension]
    run_id: Optional[str] = None
```

#### `ExposureDimension`
```python
@dataclass
class ExposureDimension:
    dimension_type: str  # strategy, state, msa, vintage, etc.
    dimension_value: str
    exposure_pct: float
    exposure_value: float
    total_portfolio_value: float
```

### Alert Management

#### Creating Thresholds
```python
from aker_portfolio import create_exposure_threshold

# Create a threshold for strategy exposure
threshold = create_exposure_threshold(
    dimension_type="strategy",
    threshold_pct=30.0,
    dimension_value="value_add",
    severity_level="warning",
    db_session=session
)
```

#### Viewing Active Alerts
```python
from aker_portfolio import get_active_alerts

alerts = get_active_alerts(db_session=session)
for alert in alerts:
    print(f"Alert: {alert.alert_message}")
    print(f"Severity: {alert.severity}")
    print(f"Status: {alert.status}")
```

### Import/Export

#### Importing Positions from CSV
```python
from aker_portfolio.import_export import PortfolioPositionImporter

csv_data = """position_id,asset_id,strategy,state,position_value
pos_1,asset_1,value_add,CA,1000000
pos_2,asset_2,core_plus,TX,1500000"""

positions = PortfolioPositionImporter.from_csv(csv_data)
```

#### Exporting Exposures to JSON
```python
from aker_portfolio.import_export import PortfolioExporter

json_data = PortfolioExporter.exposures_to_json(exposure_result)
```

## Database Schema

### Tables Created

1. **`portfolio_positions`** - Individual portfolio positions
2. **`portfolio_exposures`** - Aggregated exposure calculations
3. **`exposure_thresholds`** - Configurable alert thresholds
4. **`portfolio_alerts`** - Alert history and status

### Migration

Run the Alembic migration to create tables:
```bash
alembic upgrade head
```

## Dashboard Integration

### Visualization Data

```python
from aker_portfolio.visualization import ExposureVisualization

# Get visualization-ready data
viz = ExposureVisualization(exposure_result)
dial_data = viz.get_exposure_dials_data()
chart_data = viz.get_exposure_chart_data()
```

### Trend Analysis

```python
from aker_portfolio.visualization import ExposureTrendAnalyzer

# Analyze trends over time
trend_analyzer = ExposureTrendAnalyzer(historical_exposures)
trend_data = trend_analyzer.get_trend_data("strategy", "value_add")
```

### Comparison Tools

```python
from aker_portfolio.visualization import ExposureComparisonTool

# Compare current exposures to limits
comparison_tool = ExposureComparisonTool(exposure_result)
comparisons = comparison_tool.compare_to_limits({
    "strategy": 40.0,  # 40% max per strategy
    "state": 35.0,     # 35% max per state
})
```

## Performance Considerations

### Benchmarking

```python
from aker_portfolio.performance import PerformanceBenchmark

benchmark = PerformanceBenchmark()
result = benchmark.benchmark_exposure_calculation(positions, num_runs=5)

print(f"Average calculation time: {result['avg_time']:.3f}s")
print(f"Positions per second: {result['positions_per_second']:.0f}")
```

### Scalability Testing

```python
scalability_results = benchmark.benchmark_scalability(positions, [1, 5, 10, 20])
```

## Configuration

### Environment Variables

- `AKER_DATABASE_URL` - Database connection string
- `AKER_CACHE_PATH` - Cache directory path

### Threshold Configuration

Thresholds are configured via the database and can be managed through the API:

```python
# Example threshold configuration
{
    "dimension_type": "strategy",
    "dimension_value": "value_add",
    "threshold_pct": 30.0,
    "threshold_type": "maximum",  # or "minimum"
    "severity_level": "warning"   # or "critical"
}
```

## Error Handling

The system includes comprehensive error handling:

- **Validation errors** for invalid position data
- **Database errors** for connection issues
- **Calculation errors** for edge cases (zero portfolio value, etc.)
- **Import errors** for malformed data files

## Security Considerations

- All database operations require proper session management
- Position values are validated for positive values
- Alert messages are sanitized to prevent injection
- File imports validate data types and ranges

## Monitoring and Logging

The system integrates with the existing logging infrastructure and provides:

- Structured logging for all operations
- Performance metrics collection
- Alert generation and tracking
- Data validation reporting

## Support

For issues and questions:

1. Check the test suite for usage examples
2. Review the database schema documentation
3. Consult the API documentation
4. File issues with detailed error messages and reproduction steps
