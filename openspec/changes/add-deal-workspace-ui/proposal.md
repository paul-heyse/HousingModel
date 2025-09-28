## Why
Analysts currently have only a placeholder Deal Workspace page with no live data, navigation breadcrumbs, or ability to evaluate renovation scopes. To support UI‑003 we must deliver a real workflow that integrates the existing Dash app, newly defined deal APIs, and caching/state expectations so analysts can configure scopes, review ROI ladders, view downtime schedules, and persist scenarios.

## What Changes
- Replace the stub `deal_workspace` Dash page with a two-column workspace matching the required layout (asset summary header, scope selection with overrides, results pane with ROI ladder, downtime chart, totals, and scenario controls).
- Implement new Dash callbacks and stores to orchestrate scope selection, override debounce, ladder highlighting, and scenario persistence (including 10-minute cached scope catalog and 1.5 s idle save debounce).
- Wire GUI to new FastAPI endpoints (`/api/assets/{asset_id}`, `/api/deals/scopes/catalog`, `/api/deals/rank`, `/api/deals/scenario/*`, `/api/state-packs/impact`) and surface validation/empty/error states inline.
- Update Dash routing/navigation to support `/app/deal` with query parameters/breadcrumbs and align with existing navigation patterns.
- Add Playwright and API contract tests covering scope toggles, scenario saves, and deals/rank schema, along with validation tests for negative override handling.

## Impact
- Affected specs: gui (new capability)
- Affected code: `src/aker_gui/dash_pages/deal_workspace.py`, `src/aker_gui/dash_app.py`, `src/aker_gui/api/deals.py`, scenario caching/helpers, new state-pack impact client, Dash callbacks/tests under `tests/gui/` (Playwright) and API contract suite.
