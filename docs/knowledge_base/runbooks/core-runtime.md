# Runbook: Core Runtime Execution

## Purpose
Stand up a deterministic pipeline run (market scoring, exports, etc.) with full lineage and metrics so results are auditable and reproducible.

## Preconditions
- `.venv` activated (`source .venv/bin/activate` or micromamba shell). 
- Database reachable with migrations applied (`alembic upgrade head`).
- Environment variables populated (see `.env.example` and `Settings` fields).
- Git workspace clean or commit recorded; `RunContext` captures current SHA.

## Step-by-Step
1. **Prepare settings snapshot**
   ```bash
   python -m aker_core.config --show-effective
   ```
   Review output for unexpected defaults; export overrides as needed (`export AKER_CACHE_PATH=...`).
2. **Launch run context shell**
   ```bash
   python - <<'PY'
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.run import RunContext
   from aker_core.markets.service import PillarScoreService
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   with RunContext(Session) as run:
       service = PillarScoreService(run.session)
       service.refresh_many(as_of="2024-06-01", run_id=run.id)
       print(f"run_id={run.id}", run.git_sha, run.config_hash)
   PY
   ```
   Ensure `run_id`, `git_sha`, and `config_hash` print; errors typically mean settings or DB connectivity issues.
3. **Log lineage for external datasets**
   Inside the context, call `run.log_lineage` after each fetch:
   ```python
   run.log_lineage(
       table="market_jobs",
       source="bls_qcew",
       url="https://api.bls.gov/",
       fetched_at=load_time,
       hash=payload_hash,
   )
   ```
4. **Verify metrics endpoint (optional)**
   ```bash
   python -m aker_core.monitoring.metrics
   curl http://localhost:9000/metrics | head
   ```
   Confirm Prometheus exposition renders; investigate missing counters via `docs/knowledge_base/runbooks/core-runtime.md` troubleshooting.
5. **Persist artifacts**
   Confirm cache path (`AKER_CACHE_PATH`) contains expected parquet/json outputs and that metadata files describe content type.

## Validation
- Run `pytest tests/core/test_run_context.py tests/core/test_config.py`.
- Execute `pytest tests/test_market_score_composer.py` to ensure scoring invariants hold with new data.
- Check `runs` and `lineage` tables for entries tied to the latest `run_id`.

## Incident Response
- **Missing `run_id`**: Ensure `RunContext` context manager wraps the full execution; review stacktrace for premature exit.
- **Hash drift**: Compare `run.config_hash` to previous runs; differences imply config changes. Use `git diff` and attach explanation to governance checklist.
- **Metrics server failure**: Verify `prometheus-client` installed; runbook `metrics` section covers reinstall steps.

## References
- Capability brief: [capabilities/core-runtime.md](../capabilities/core-runtime.md)
- Spec: `openspec/specs/core/spec.md`
- Change log: `runs` table entries filtered by `run_id`

