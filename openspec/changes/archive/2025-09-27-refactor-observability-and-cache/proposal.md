## Why
Recent work surfaced optimizations we should address before layering new features: structured logging still has avoidable overhead and limited endpoint clarity, cache base-path overrides need hardening, run-context sessions recreate engines on hot paths, and our Prefect deployment module leans on deprecated APIs. Tackling these together keeps observability and orchestration stable.

## What Changes
- Refine `aker_core.logging` (lightweight tracemalloc guard, clearer Prometheus helper behaviour, label normalization) and publish usage docs in README.
- Strengthen `aker_core.cache` (robust type inference, metadata helper, refreshed singleton when env overrides change) and adjust tests.
- Cache flow engines/session factories inside `with_run_context` to avoid per-call `create_engine`; ensure run status is persisted on meta-session errors.
- Switch `flows/deployments.py` to Prefect 3 `flow.deploy()` / `serve()` patterns and prune deprecated imports; add smoke checks.
- Align Prefect dependency range in `pyproject.toml` with runtime 3.x.

## Impact
- Affected specs: core/logging, core/cache, core/orchestration
- Affected code: `src/aker_core/logging.py`, `src/aker_core/cache.py`, `src/aker_core/run.py`, `flows/deployments.py`, `README.md`, tests.
