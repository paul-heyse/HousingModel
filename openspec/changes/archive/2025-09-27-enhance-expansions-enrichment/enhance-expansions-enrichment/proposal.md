## Why
The initial expansions ingestor delivers baseline RSS parsing and heuristics, but analysts still need richer context and observability to trust the feed. Enhanced entity recognition, geocoding, and pipeline monitoring will improve data quality, reduce manual review effort, and surface stale or failing sources before they impact market models.

## What Changes
- Enrich `ExpansionEvent` with NLP-driven company/location extraction, industry tagging, and geocoding.
- Introduce anomaly scoring and historical benchmarking to flag outliers for analyst review automatically.
- Emit structured metrics, logs, and persistence hooks that track feed health, throughput, and review queue volumes.
- Surface manual review outputs via Prefect/logging artefacts so analysts can triage low-confidence events quickly.

## Impact
- Affected specs: etl/ingestion
- Affected code: `aker_core/expansions/`, monitoring/metrics integration, Prefect flow wiring, data lake lineage.
