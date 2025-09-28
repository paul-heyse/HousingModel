# Capability: GUI Analytics

## Objective
Expose market, deal, risk, and operational analytics through an analyst-friendly Dash interface so non-developers can explore scenarios, export results, and trigger refreshes without touching code.

## Key Outcomes
- Multi-page Dash app (`src/aker_gui/dash_app.py`) orchestrates navigation, layout, and session stores for market scorecards, deal workspace, asset fit wizard, risk panel, operations, and data refresh screens.
- Page modules under `src/aker_gui/dash_pages/` encapsulate layout + callbacks, delegating heavy analytics to `aker_core` services.
- REST endpoints in `src/aker_gui/api/` expose JSON payloads for asynchronous components and Excel export triggers.
- Static assets (`src/aker_gui/static/`) and design system components (`src/aker_gui/components/`) ensure consistent branding and accessibility.

## Architecture Snapshot
- **Entry Points**: `aker_gui.app:create_app`, `aker_gui.dash_app.create_dash_app`, page-level `register_callbacks` functions.
- **Dependencies**: Dash, dash-bootstrap-components, Plotly, Leaflet, FastAPI (hosting), `aker_core` service layer, Postgres.
- **Integrations**: Auth via future SSO (placeholder), export triggers call `aker_core.exports.to_excel`, score refresh icons call Prefect API.

## Operational Workflow
1. Application boots through `aker_gui.app:run` (FastAPI + Dash mounted application) with `Settings()` loaded for environment config.
2. On navigation, `dcc.Location` drives router to load page-specific layout and register callbacks.
3. Callbacks fetch data via `aker_gui.services.*` modules that wrap `aker_core` queries and orchestrate caching.
4. Analysts explore charts/tables, run asset fit simulations, trigger exports, and download outputs; sessions stored in `dcc.Store` for continuity.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| `aker_core` APIs | Scorecard & analytics data | Real-time | Accessed via services module with caching to reduce DB load.
| Prefect/ETL status endpoints | ETL freshness | Minute-level polling | Surfaces pipeline state within Data Refresh page.
| `exports/` directory | Generated workbooks | On demand | Download links provided post-generation.

## Validation & QA
- `tests/test_ops_brand_dashboard.py` exercises dashboard assembly and callback invariants for the Ops & Brand surface.
- GUI automation coverage is expanding; interim smoke tests run through manual checklist documented in the GUI runbook while Playwright suites are scoped in `openspec/changes/add-ops-brand-dashboard`. 
- Manual QA uses the GUI runbook alongside golden dataset snapshots.

## Runbooks
- [Gui Analytics](../runbooks/gui-analytics.md)

## Change Log
- 2024-06-04 — Initial GUI knowledge base entry documenting navigation and service integration.

