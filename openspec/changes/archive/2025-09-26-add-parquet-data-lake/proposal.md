## Why
Implement a partitioned Parquet data lake to store and version raw/cleaned datasets with Hive-style partitioning for efficient querying and schema evolution tolerance. This enables scalable data storage for the Aker platform beyond the core PostgreSQL schema, supporting time-series analytics and dataset lineage.

## What Changes
- Introduce `aker_data.lake` module with `write(df, dataset, as_of, partition_by)` and `read(dataset, as_of=None, filters={})` functions.
- Implement Hive-style partitioning: `/lake/{dataset}/as_of=YYYY-MM/partitions/*.parquet`.
- Support schema evolution with backward compatibility for dataset versions.
- Add Great Expectations suite integration for data quality validation.
- Provide partition-aware reading with predicate pushdown for performance.

## Impact
- Affected specs: data/lake
- Affected code: `src/aker_data/lake.py`, data ingestion pipelines, lineage tracking.
