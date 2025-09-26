## 1. Implementation
- [x] 1.1 Define `aker_core.run.RunContext` to capture git SHA, config hash, deterministic seeds, start/end timestamps, and assign `run_id`.
- [x] 1.2 Persist run metadata to `runs` table and ensure all data outputs reference the active `run_id`.
- [x] 1.3 Implement `run.log_lineage(...)` helper that writes lineage rows with table, source, URL, fetched_at, and hash details.
- [x] 1.4 Add golden test covering sample pipeline run and rerun determinism (hash and outputs match).
- [x] 1.5 Update developer docs/examples to illustrate run context usage and lineage expectations.
