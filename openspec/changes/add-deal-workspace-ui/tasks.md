## 1. Routing & Layout
- [x] 1.1 Update Dash routing (`dash_app.py`) to serve `/app/deal` with breadcrumb support and query parsing for `asset_id`, `msa_id`, `as_of`.
- [x] 1.2 Rebuild `deal_workspace.create_layout` with header summary card, left scope selection (grouped checklist + override inputs + control buttons), right results column (ROI ladder table, downtime chart, totals, scenario actions).

## 2. State & Callbacks
- [x] 2.1 Introduce `dcc.Store(id="deal_workspace_state")` with idle debounce saves (1.5 s) and scope catalog caching (10-minute TTL).
- [x] 2.2 Implement Dash callbacks for scope/override changes (POST `/api/deals/rank`), state-pack adjustments, ROI ladder row highlighting, warning display, and scenario persistence flows (`Save`, `Save As`, list refresh).

## 3. API Layer
- [x] 3.1 Flesh out FastAPI endpoints (`assets`, `deals/scopes/catalog`, `deals/rank`, `deals/scenario*`, `state-packs/impact`) with pydantic schemas matching the contracts; add caching hooks where required.
- [x] 3.2 Add client helpers/shared typing in `src/aker_gui/api/__init__.py` or dedicated service layer for reuse across callbacks.

## 4. Testing & Telemetry
- [ ] 4.1 Add Playwright tests: toggling scope reorders ladder; scenario save persists and appears in recent list.
- [ ] 4.2 Add API contract tests validating `deals/rank` response fields/ordering and negative override validation.
- [ ] 4.3 Emit telemetry counters (scope selections, iterations, save events) and show admin debug badge with backend compute time; ensure logging pathways are in place.
