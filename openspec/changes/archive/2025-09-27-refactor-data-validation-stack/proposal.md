## Why
Great Expectations has become a maintenance bottleneck across the data pipelines, adds heavy runtime dependencies, and duplicates validation logic already implemented with Pydantic models. Migrating to a cohesive stack of Pydantic (configuration/runtime DTOs), Pandera (DataFrame schema + statistical validation), and Marshmallow (serialization/external payload validation) will reduce complexity, improve developer ergonomics, and align the project with actively supported libraries.

## What Changes
- Replace Great Expectations usage with Pandera-based DataFrame validation across ETL pipelines while leveraging Pydantic models for config/runtime contracts and Marshmallow schemas for API I/O.
- Update validation orchestration, observability hooks, and developer tooling to reflect the new stack (type stubs, docs, lint/test gates).
- Provide migration guidance and compatibility shims so existing suites/tests transition without regressions.

## Impact
- Affected specs: core (data validation + observability requirements)
- Affected code: `aker_core.validation`, ETL flows, Prefect tasks, testing utilities, CI configuration, documentation.
