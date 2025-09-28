## 1. Data Lake Validation Fixes
- [x] 1.1 Refactor geometry validation branch in `DataLake.write` to use validity rate/correction stats instead of `.success` and handle CRS dictionary outputs safely.
- [x] 1.2 Add regression tests covering successful GeoDataFrame writes, invalid geometry warnings, and CRS mismatch paths.

## 2. Supply ETL Test Harness
- [x] 2.1 Import the proper HTTP error type in `tests/etl/test_supply_etl.py` and assert the failure code path.

## 3. Quality Gates
- [x] 3.1 Run `ruff` (or update lint allow-list) plus full `pytest -q` to confirm the fixes.
