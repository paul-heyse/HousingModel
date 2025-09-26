## 1. Implementation
- [ ] 1.1 Create `aker_data.lake` module with write/read functions and partitioning logic.
- [ ] 1.2 Implement Hive-style path conventions: `/lake/{dataset}/as_of=YYYY-MM/partitions/`.
- [ ] 1.3 Add schema evolution support with PyArrow/Parquet compatibility checks.
- [ ] 1.4 Integrate Great Expectations suite for data quality validation on write.
- [ ] 1.5 Add partition-aware reading with predicate pushdown using DuckDB or similar.
- [ ] 1.6 Update lineage tracking to log data lake operations.
- [ ] 1.7 Add comprehensive tests for partitioning, schema evolution, and GE integration.
