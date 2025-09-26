## Why
Recent logging and caching enhancements (structlog integration, Prometheus metrics, cache path handling) landed without targeted regression tests. We need coverage to guard against regressions and to validate required Prometheus endpoints.

## What Changes
- Add unit tests for `aker_core.logging` covering labeled timings, Prometheus endpoint helpers, and structured error metadata.
- Add cache tests for inferred base path, JSON storage metadata, and environment overrides.
- Add smoke tests for Prefect deployments to catch misconfiguration early.

## Impact
- Affected specs: core/logging, core/cache
- Affected code: `tests/core/test_logging_module.py`, `tests/test_cache.py`, `flows/deployments.py`, possible helper fixtures.
