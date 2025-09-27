# HousingModel (replace via scripts/init.sh)

Baseline template for Python projects in Cursor on Ubuntu.

## Quick start (per project)
1. Run `scripts/init.sh <package_name> [python_version] "Description"`.
2. Open folder in Cursor (`cursor .`).
3. Ensure interpreter shows `.venv/bin/python`.
4. Run target tasks: **pytest**, **lint**, **format**.
5. See `docs/innovation_jobs.md` for innovation/jobs analytics usage examples.

See `.cursor/rules`, `.vscode/*`, and `environment.yml` for configuration details.

## Runtime configuration & feature flags

The core application settings live in `aker_core.config.Settings`, which follows 12-factor
precedence (`env` > `.env` > defaults) using `pydantic-settings`. Instantiate `Settings()` to
access typed configuration for databases, external APIs, and feature flags. Secrets remain out of
snapshots when you call `settings.snapshot()`.

To toggle behaviour without code changes, use `aker_core.flags.is_enabled("FLAG_NAME")`. Flag
values resolve from the same Settings instance and are surfaced via
`aker_core.config.build_run_config()` so pipelines can persist them into `runs.config_json`.

## Run metadata & lineage

Wrap every pipeline in `with aker_core.run.RunContext(session_factory) as run:` to capture git SHA,
configuration hash, deterministic seeds, and start/end timestamps. Use `run.log_lineage(...)` to
record external dataset usage and `run.set_output_hash(...)` to persist golden hashes that make
reruns auditable. The provided SQLAlchemy session (`run.session`) should be used to write outputs so
each record can carry `run_id`.

## Plugin registry & ports

Core workflows depend on the abstract ports under `aker_core.ports` (`MarketScorer`,
`AssetEvaluator`, `DealArchetypeModel`, `RiskEngine`). Register concrete adapters with
`aker_core.plugins.register("adapter_name", factory)` or expose them via the
`aker_core.plugins` entry-point group so `aker_core.plugins.discover()` can auto-load them.
Tests can hot-swap implementations using `aker_core.plugins.override(...)` without touching
production wiring.

## Market score composition

The four market pillars (Supply, Jobs, Urban, Outdoors) now roll up through the deterministic
composer in `aker_core.markets.composer`. Import the helper with
`from aker_core.markets.composer import score as compose_market_score` to normalise pillar weights
(defaults to 0.3/0.3/0.2/0.2), persist both 0–5 and 0–100 composites, and record provenance (`weights`,
`score_as_of`, `run_id`) on the `pillar_scores` row. Batch workflows can process multiple markets at
once via `from aker_core.markets.composer import score_many` which the
`MaterializedTableManager` uses when refreshing analytics so missing composites are filled before
downstream exports.

> Golden-master regression for the composer/service lives in `tests/test_market_score_service.py` and
> compares the computed scores to the canonical snapshot stored under `tests/data/`. For quick
> throughput checks, run `pytest tests/perf/test_market_scoring_perf.py -q` to record timing metadata
> for a 250-market batch refresh.

Normalising pillar metrics in bulk is supported via `aker_core.markets.pipeline`; run
`run_scoring_pipeline(raw_metrics)` to perform the end-to-end
normalisation → pillar 0–5 conversion → weighted composite score, or import individual helpers such as
`normalise_metrics` and `composite_scores` for customised flows.

Typical usage::

    from aker_core.markets.pipeline import run_scoring_pipeline

    raw_metrics = {
        "supply": [12.5, 18.0, 27.4, 31.6],
        "jobs": [42.0, 55.2, 78.9, 90.0],
        "urban": [68.0, 72.5, 83.0, 91.0],
        "outdoor": [58.0, 64.0, 70.0, 80.0],
    }
    result = run_scoring_pipeline(raw_metrics)
    print(result.composite_0_5)

**Troubleshooting**

- ``RobustNormalizationError: Input array is empty`` – ensure each metric list contains at least one
  finite observation before calling the pipeline.
- ``percentiles must satisfy 0 <= p_low < p_high <= 1`` – check custom percentile arguments; the
  defaults ``p_low=0.05`` / ``p_high=0.95`` usually provide good winsorisation.
- Outputs include ``NaN`` – the input contained ``NaN`` or infinite values; clean the source data or
  fill missing values before normalisation.

**Performance tips**

- The implementation is vectorised; pass NumPy arrays (or structures convertible via ``np.asarray``)
  for best throughput.
- For very large batches (>500k rows) reuse a seeded ``np.random.Generator`` to create synthetic test
  data when profiling. The `tests/perf/test_normalization_perf.py` benchmark ensures a 500k-row run
  completes within ~1s on the reference hardware.

## Structured logging & metrics

Use `aker_core.logging.get_logger(__name__)` to emit JSON logs via `structlog`:

```python
from aker_core.logging import get_logger, log_timing, start_metrics_server

logger = get_logger(__name__)
logger.info("scored_market", msa="DEN", ms=42)

with log_timing(logger, "load_osm", metric_name="load_osm_seconds"):
    load_data()

start_metrics_server(port=9000)  # exposes Prometheus metrics on /metrics
```

The helpers integrate with Prometheus (`prometheus_client`) for counters and histograms and include
an error taxonomy (`classify_error`, `log_classified_error`) so downstream systems can filter by
`error_type`, `error_code`, `category`, and `severity`. Metrics can also be exported manually via
`aker_core.logging.generate_metrics()` or mounted with `aker_core.logging.make_metrics_app()`.

## Data layer: DSN patterns and dev setup

- Production (PostGIS): set `AKER_POSTGIS_DSN` in environment or `.env`.
  - Example: `postgresql+psycopg://user:pass@db-host:5432/aker`.
- Development (SQLite/SpatiaLite optional): use SQLite for quick local runs and CI.
- Example: `sqlite+pysqlite:///./local.db`.
- Geometry fields:
  - PostgreSQL: true PostGIS geometry columns.
  - SQLite: fallback TEXT columns (WKT/WKB strings) for tests; enable SpatiaLite in your local environment if needed.

### Materialized analytics tables

- `market_analytics` captures pre-computed market metrics (pillar scores, supply/job signals, and census aggregates) keyed by `period_month` and refreshed via the `flows.refresh_materialized_tables` Prefect flow.
- `asset_performance` records per-asset scoring, market rollups, and rank-in-market for downstream BI.
- Both tables are refreshed together, validated with Great Expectations suites (`market_analytics_validation`, `asset_performance_validation`), and exposed through helper views `market_supply_joined` and `asset_scoring_joined` for complex joins.
- Schedule the refresh with the provided Prefect deployment (`materialized-analytics-refresh`) or trigger manually: `from flows import refresh_materialized_tables; refresh_materialized_tables()`.

Running migrations locally with SQLite:

```bash
. .venv/bin/activate
alembic upgrade head
```

## Data Lake

The platform includes a partitioned Parquet data lake for storing and versioning raw/cleaned datasets with Hive-style partitioning:

```python
from aker_data.lake import DataLake

# Create data lake instance
lake = DataLake(base_path="/path/to/lake")

# Write partitioned dataset
df = pd.DataFrame({"id": [1, 2], "state": ["CA", "NY"], "value": [100, 200]})
lake.write(df, "income_data", "2025-06", partition_by=["state"])

# Read with time and column filters
filtered_data = lake.read("income_data", as_of="2025-06", filters={"state": "CA"})

# List datasets and partitions
datasets = lake.list_datasets()
partitions = lake.list_partitions("income_data")
```

**Features:**
- Hive-style partitioning: `/lake/{dataset}/as_of=YYYY-MM/partitions/`
- Schema evolution support with backward compatibility
- Great Expectations integration for data quality validation
- Partition-aware reading with predicate pushdown using DuckDB
- Lineage tracking for all data lake operations

## Cache & Rate Limiting

The platform includes intelligent HTTP caching and rate limiting for external data dependencies:

```python
from aker_core.cache import Cache, RateLimiter, fetch

# HTTP response caching with ETag/Last-Modified support
cache = Cache(base_path="/data")
response = cache.fetch("https://api.example.com/data", ttl="1h")

# Rate limiting with exponential backoff
limiter = RateLimiter(token="epa_airnow", requests_per_minute=60)
@limiter.wrap
def api_call():
    return requests.get("https://api.epa.gov/airnow/")

# Convenience function
response = fetch("https://api.example.com/data", ttl="30m")
```

**Features:**
- **HTTP Caching**: ETag/Last-Modified header support with conditional requests
- **Rate Limiting**: Token bucket algorithm with exponential backoff and jitter
- **Local Storage**: Organized storage for Parquet, GTFS, and OSM data with TTL
- **Offline Mode**: Automatic detection and graceful degradation when network unavailable
- **Lineage Tracking**: All cache operations logged to lineage table

**Storage Organization:**
```
/data/
  parquet/{dataset}/          # Processed data files
  gtfs/{dataset}/            # GTFS transit data
  osm/{dataset}/             # OpenStreetMap data
  http_cache/                # SQLite cache for HTTP responses
```

## Geospatial Standards & CRS Utilities

The platform enforces consistent coordinate reference systems and validates spatial data integrity:

```python
from aker_geo.crs import to_ui, to_storage
from aker_geo.validate import validate_geometry

# Transform for web mapping (EPSG:3857)
ui_gdf = to_ui(storage_gdf)  # Storage CRS → UI CRS

# Transform for storage (EPSG:4326)
storage_gdf = to_storage(ui_gdf)  # UI CRS → Storage CRS

# Validate geometry data
validation_report = validate_geometry(gdf)
print(f"Valid: {validation_report.valid_count}, Invalid: {validation_report.invalid_count}")
```

**Features:**
- **CRS Standards**: EPSG:4326 for storage, EPSG:3857 for UI display
- **Geometry Validation**: Automatic detection and correction of invalid geometries
- **PostGIS Integration**: SRID enforcement and spatial data integrity
- **Coordinate Transformations**: Accurate CRS conversions with metadata preservation
- **Spatial Operations**: CRS-aware spatial joins, distance calculations, and area computations

**CRS Standards:**
- **Storage CRS**: EPSG:4326 (WGS84) - Geographic coordinates for data storage
- **UI CRS**: EPSG:3857 (Web Mercator) - Projected coordinates optimized for web mapping
- **Validation**: Automatic CRS detection and correction for spatial data integrity

## ETL Orchestration

The platform uses Prefect for robust ETL pipeline orchestration with automated scheduling and monitoring:

```python
from prefect import flow, task
from aker_core.cache import fetch
from aker_data.lake import lake

@flow
def refresh_market_data():
    """Orchestrate market data ingestion and transformation."""
    # Ingest external data with caching
    response = fetch("https://api.census.gov/data", ttl="1d")
    raw_data = response.json()

    # Transform and store in data lake
    df = transform_census_data(raw_data)
    lake.write(df, "census_income", "2025-01")

@flow
def score_all_markets():
    """Score all markets using latest data and models."""
    # Load market data from data lake
    market_data = lake.read("census_income", as_of="2025-01")

    # Apply scoring models
    scores = score_markets(market_data)

    # Export results
    export_market_scores(scores)

# Schedule flows
refresh_market_data.schedule = "0 6 * * *"  # Daily at 6 AM
score_all_markets.schedule = "0 8 * * 1"   # Weekly on Monday at 8 AM
```

**Features:**
- **Flow Templates**: Reusable patterns for ingestion, transformation, scoring, and export
- **Configurable Scheduling**: Cron expressions and interval-based triggers
- **State Persistence**: Full execution history with Prefect backend integration
- **Error Handling**: Automatic retries with exponential backoff
- **Local Development**: Test flows locally before deployment
- **Monitoring**: Integration with structured logging and metrics

## Data Quality & Validation

The platform enforces data quality through Great Expectations validation suites with automated quality gates:

```python
from aker_core.validation import validate_data_quality

# Validate data in ETL flows
validation_result = validate_data_quality(
    df=market_data,
    suite_name="market_data_validation",
    fail_on_error=True
)
```

**Quality Gates:**
```bash
# CI/CD quality gate validation
python scripts/validate_quality_gate.py acs data/market_data.csv

# List available validation suites
python scripts/validate_quality_gate.py --list-suites

# Validation with detailed reporting
python scripts/validate_quality_gate.py market_data data/scores.parquet --output results.json
```

**Features:**
- **Schema Validation**: Column existence, types, and nullability checks
- **Range Validation**: Numeric ranges, categorical values, and temporal bounds
- **Referential Integrity**: Foreign key relationships and cross-table consistency
- **Coverage Validation**: Geographic and temporal data coverage requirements
- **CI/CD Integration**: Quality gates that prevent deployment of invalid data
- **Automated Monitoring**: Continuous validation with alerting on failures
