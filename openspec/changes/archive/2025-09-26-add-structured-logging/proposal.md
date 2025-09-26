## Why
Implement structured logging and metrics collection to provide observability into pipeline execution, performance monitoring, and error tracking. This enables operational visibility for production deployments with JSON-structured logs and optional Prometheus metrics integration.

## What Changes
- Introduce `aker_core.logging` module with structlog-based JSON logging.
- Add timing decorators and context managers for performance measurement.
- Implement error taxonomy with structured error codes and categories.
- Provide Prometheus metrics integration with counters and histograms.
- Add log field validation and structured output to STDOUT.

## Impact
- Affected specs: core/logging
- Affected code: `src/aker_core/logging.py`, all pipeline modules, error handling, metrics collection.
