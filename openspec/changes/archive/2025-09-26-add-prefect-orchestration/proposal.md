## Why
Data pipeline orchestration is currently manual and ad-hoc, requiring developers to manually trigger ingestion, transformation, and scoring processes. This leads to inconsistent execution, poor error handling, and difficulty in monitoring pipeline health. Prefect provides a robust orchestration framework for reliable, scheduled, and monitored data workflows.

## What Changes
- Introduce Prefect project structure with flow scaffolding for ETL pipelines.
- Create reusable flow templates for data ingestion, transformation, scoring, and export operations.
- Implement configurable scheduling with cron expressions and interval-based triggers.
- Add state persistence and flow run tracking with Prefect's backend integration.
- Provide local development and testing capabilities for flows.

## Impact
- Affected specs: etl/orchestration
- Affected code: `flows/refresh_market_data.py`, `flows/score_all_markets.py`, orchestration infrastructure, pipeline scheduling.
