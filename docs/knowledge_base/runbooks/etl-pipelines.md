# Runbook: ETL Pipeline Operations

## Purpose
Execute and monitor ETL flows that populate market, jobs, hazard, and amenity datasets powering downstream analytics.

## Preconditions
- `.venv` activated with required dependencies (`micromamba run -p ./.venv pip install -r requirements.txt` if missing packages).
- `AKER_POSTGIS_DSN` / secrets configured for source APIs (Census, BLS, vendor feeds, Mapbox, etc.).
- Prefect API reachable if running in orchestrated mode (`AKER_PREFECT_API_URL`).
- Data lake storage (`AKER_CACHE_PATH` or `DataLake` base path) writable.

## Step-by-Step
1. **Dry-run in local mode**
   ```bash
   python -m flows.refresh_market_data 2023 2024-06
   ```
   Inspect console output for fetch/transform/store steps. Failures typically indicate credential or schema drift.
2. **Run hazard refresh**
   ```bash
   python - <<'PY'
   from flows.refresh_hazard_metrics import refresh_hazard_metrics
   refresh_hazard_metrics(as_of="2024-06")
   PY
   ```
   Confirms slope/wildfire/water stress datasets updated. Validate resulting parquet partitions in cache or S3.
3. **Trigger amenity benchmarks**
   ```bash
   python - <<'PY'
   from flows.refresh_amenity_benchmarks import refresh_amenity_benchmarks
   refresh_amenity_benchmarks(as_of="2024-06")
   PY
   ```
   Ensure vendor API keys are set; watch log for rate limiting and consult vendor SLA if repeated.
4. **Register/submit Prefect run (optional)**
   ```bash
   prefect deployment run "refresh-market-data/local" --params '{"year": "2023", "as_of": "2024-06"}'
   ```
   Requires Prefect deployment definitions; check Prefect UI for run state.
5. **Backfill historical data**
   Use flow-level parameterization in a loop:
   ```bash
   for year in 2019 2020 2021 2022; do
       python -m flows.refresh_market_data "$year" "$year-12"
   done
   ```
   After each run, log lineage via `run.log_lineage` in flow (already instrumented) and verify partitions under `data_lake/census_income`.
6. **Validate outputs**
   ```bash
   pytest tests/test_expansions_ingestor.py tests/test_boundary_geocoding_etl.py
   ```
   Run additional suites relevant to the pipelines you executed. Review generated Great Expectations reports if validation failures occur.

## Validation
- Confirm new partitions show up in target tables (e.g., `SELECT DISTINCT data_year FROM market_jobs`).
- Check Great Expectations / Pandera reports stored alongside data lake outputs.
- Prefect UI should show `State=Completed`; investigate `Failed` or `Cancelled` states.

## Incident Response
- **API Rate limiting**: flows retry with exponential backoff; if still failing, pause schedule and follow vendor-specific rate limit guidance in `docs/sources_supplement.yml`.
- **Schema drift**: Update Pandera schema definitions and spec entries, then rerun validation.
- **Data lake write failure**: Verify `AKER_CACHE_PATH` permissions and available disk. Clear partial partitions before rerun.

## References
- Capability brief: [capabilities/etl-pipelines.md](../capabilities/etl-pipelines.md)
- Source manifest: `sources.yml`, `sources_supplement.yml`
- Spec: `openspec/specs/etl/spec.md`

