## 1. Validation Stack Migration
- [x] 1.1 Inventory current Great Expectations suites/tests and map to equivalent Pydantic/Pandera/Marshmallow responsibilities
- [x] 1.2 Implement Pandera schema modules for each persisted DataFrame/Parquet table with coverage parity to existing GE suites
- [x] 1.3 Extend Pydantic models and Marshmallow schemas to cover config/runtime and API serialization gaps uncovered during migration

## 2. Pipeline & Tooling Updates
- [x] 2.1 Refactor Prefect/ETL tasks to invoke the new validation stack and remove GE-specific orchestration
- [x] 2.2 Update observability hooks, docs, and developer setup (dependencies, lint/type/test configs) to reflect the new libraries
- [x] 2.3 Provide migration utilities or shims for any downstream jobs still expecting GE artifacts

## 3. Quality Gates
- [x] 3.1 Backfill tests ensuring Pandera validations gate bad data and mirror previous GE expectations
- [x] 3.2 Refresh CI pipelines to run the new validation checks and remove GE runners
- [x] 3.3 Document rollout plan and training material for the updated validation workflow
