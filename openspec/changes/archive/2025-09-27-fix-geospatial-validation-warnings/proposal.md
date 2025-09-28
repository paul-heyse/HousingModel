## Why
Recent regression testing uncovered that the refactored validation stack broke geospatial safeguards in the data lake (the new `GeometryValidationResult` no longer exposes `.success`, and CRS checks changed shape). As a result, every geometry write now logs warnings and silently skips validation. We also spotted a supply ETL test stub raising `requests.HTTPError` without importing `requests`, so failures raise `NameError` instead of exercising the error path.

## What Changes
- Repair `DataLake.write` geospatial validation so it consumes the new Pandera-backed helpers without false negatives and continues to log actionable diagnostics.
- Add regression coverage that writes a valid GeoDataFrame and asserts no warnings are emitted, plus guard tests for CRS edge cases.
- Fix the supply ETL dummy client to import the exception type it raises and extend tests to cover the failure branch.
- Run lint/test tooling to ensure no new regressions.

## Impact
- Affected specs: core
- Affected code: `src/aker_data/lake.py`, `src/aker_geo/validate.py` (only if helper additions needed), `tests/etl/test_supply_etl.py`, new regression tests under `tests/data_lake/`.
