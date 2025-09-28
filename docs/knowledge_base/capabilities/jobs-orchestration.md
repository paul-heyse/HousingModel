# Capability: Jobs & Innovation Metrics

## Objective
Quantify innovation-economy strength—location quotients, growth rates, migration, research awards, business formation—and persist the metrics that feed market scoring and IC narratives.

## Key Outcomes
- `aker_jobs.metrics.lq` and `aker_jobs.metrics.cagr` compute location quotients and compound annual growth rates with rigorous validation.
- Migration, awards, and business formation helpers in `aker_jobs.timeseries` and `aker_jobs.sources` orchestrate Census, IRS, NIH/NSF/DoD ingestion.
- Aggregated results populate `aker_data.models.MarketJobs` via ETL flows, keyed by `msa_id`, `as_of`, and metric lineage.
- Expansion surveillance integrates with `aker_core.expansions.ExpansionsIngestor` to capture qualitative demand signals.

## Architecture Snapshot
- **Entry Points**: `aker_jobs.metrics.lq`, `aker_jobs.metrics.cagr`, `aker_jobs.timeseries.calculate_net_migration`, `aker_jobs.metrics.build_market_jobs_record`.
- **Data Sources**: BLS CES/QCEW, Census LODES, IRS migration, NIH/NSF award APIs, Census BFS microdata.
- **Dependencies**: Pandas, NumPy, Pydantic models for validation, SQLAlchemy for persistence.
- **Integrations**: Market scoring service consumes results via `MarketJobs` table; exports workbook references metrics in Market Scorecard sheet.

## Operational Workflow
1. ETL pipelines refresh jobs-related raw datasets and materialized views.
2. Metric builders normalise inputs (per 100k population, inflation adjustments) and compute LQ/CAGR/migration values.
3. Aggregated metrics inserted into `market_jobs` with provenance metadata and inserted/updated timestamps.
4. Market scoring composer joins `market_jobs` to derive innovation pillar contributions; exports and GUI surfaces reference the same tables.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| BLS CES/QCEW | Employment levels | Monthly | Pulled via BLS API with metadata captured in lineage table.
| Census LODES | Workforce inflow/outflow | Annual | Used for commuting + net migration adjustments.
| IRS migration | Net migration calculations | Annual | Age-band filtering applied to isolate 25-44 cohort.
| NIH/NSF/DoD APIs | Research funding | Quarterly | API keys stored in secrets manager; responses cached for 24h.
| Census BFS | Business formation | Monthly | Processed through ETL to compute startup density and survival rates.

## Validation & QA
- `tests/test_market_score_service.py` verifies innovation inputs feed scoring composer correctly.
- `tests/jobs/test_jobs_analysis.py`, `tests/jobs/test_jobs_sources.py`, and `tests/jobs/test_jobs_validation.py` cover metric helpers, source ingestion, and validation edge cases.
- Data quality checks executed via Great Expectations suites referenced in ETL runbook.

## Runbooks
- [Jobs Orchestration](../runbooks/jobs-orchestration.md)

## Change Log
- 2024-06-04 — Jobs capability documentation established covering metric computation and data lineage.

