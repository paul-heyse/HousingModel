## Why
Decision makers need tamper-evident audit trails for every model execution. Today, runs lack deterministic seeds, lineage logging, and immutable context so reruns cannot be proven identical.

## What Changes
- Introduce a `aker_core.run.RunContext` context manager that captures git SHA, configuration hash, seeds, timestamps, and assigns a run identifier.
- Persist run metadata in `runs` and related lineage records in `lineage` tables, ensuring every output carries `run_id`.
- Provide helpers to log dataset lineage, enforce deterministic seeds, and validate reruns against stored hashes with golden run tests.

## Impact
- Affected specs: core
- Affected code: `aker_core/run.py`, persistence layer for `runs` and `lineage`, pipeline hooks and tests.
