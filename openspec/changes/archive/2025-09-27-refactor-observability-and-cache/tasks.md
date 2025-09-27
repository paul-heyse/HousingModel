## 1. Observability
- [x] 1.1 Lighten logging timer stack (lazy tracemalloc) and normalize Prometheus assists.
- [x] 1.2 Update README with structured logging + metrics guidance.

## 2. Cache hardening
- [x] 2.1 Improve base-path override & metadata helper in `aker_core.cache`.
- [x] 2.2 Refresh tests covering env override and JSON inference.

## 3. Run context & deployments
- [x] 3.1 Reuse engines/session factories inside `with_run_context`.
- [x] 3.2 Migrate Prefect deployments to 3.x API and smoke test.
- [x] 3.3 Update Prefect dependency range in pyproject.
