## ADDED Requirements
### Requirement: Deal Workspace Navigation
The GUI SHALL expose a Deal Workspace reachable at `/app/deal` that honours query parameters (`asset_id`, `msa_id`, `as_of`) and displays breadcrumb navigation "Deals → Workspace".

#### Scenario: Route With Query Parameters Loads Workspace
- **WHEN** the analyst navigates to `/app/deal?asset_id=AKR-123&msa_id=BOI&as_of=2025-09`
- **THEN** the Deal Workspace page SHALL render with breadcrumb "Deals → Workspace" and fetch asset + scope data for the supplied identifiers

### Requirement: Scope Selection & Overrides
The Deal Workspace SHALL present multi-select scopes grouped by category with inline override inputs (cost_per_door, expected_lift, downtime_wk) and action buttons (Reset overrides, Apply state pack adders).

#### Scenario: Override Validation Blocks Invalid Input
- **WHEN** an analyst enters a negative `cost_per_door` override
- **THEN** the UI SHALL show inline validation (red text) and block the rank API call until corrected

### Requirement: ROI Ladder & Downtime Results
Selecting scopes or editing overrides SHALL trigger a rank request updating the ROI ladder (sortable, shows NPV/IRR/payback, warning icon if payback exceeds mandate) and a downtime schedule chart that highlights selected ladder rows in the scope list.

#### Scenario: Ladder Update After Scope Toggle
- **WHEN** an analyst toggles a scope on
- **THEN** the UI SHALL POST `/api/deals/rank`, update the ladder sorted by `roi_rank`, refresh the downtime chart, and highlight the selected ladder row in the scope checklist

### Requirement: State Management & Caching
Scenario selections SHALL be stored in `dcc.Store(id="deal_workspace_state")` with a 1.5-second idle debounce before save; the scope catalog SHALL be cached for 10 minutes to avoid repeated fetches.

#### Scenario: Debounced Save After Idle Period
- **WHEN** the analyst stops editing for 1.5 seconds
- **THEN** the current scenario state SHALL auto-save (POST `/api/deals/scenario save`) while the ladder remains untouched during the debounce

### Requirement: Scenario Persistence
The workspace SHALL support saving, saving-as, listing the last five scenarios, and loading saved scenarios via `/api/deals/scenario/{scenario_id}`.

#### Scenario: Saved Scenario Appears In Recent List
- **WHEN** the analyst saves a named scenario
- **THEN** the backend SHALL respond with `{scenario_id, saved_at}` and the scenario list SHALL refresh with the new entry at the top

### Requirement: Telemetry & Admin Indicator
The GUI SHALL log telemetry events (scope selection count, ladder recompute count, scenario saves) and display an admin-only badge with the last backend compute time.

#### Scenario: Admin Sees Debug Badge
- **WHEN** an admin is authenticated
- **THEN** the workspace header SHALL show a small "debug" badge including the most recent backend compute duration for the ladder request

### Requirement: Tests & Contracts
Automated tests SHALL verify UI behaviour and API contract compliance for the deal workspace interactions.

#### Scenario: Playwright Scope Toggle Test
- **WHEN** the Playwright test toggles a scope
- **THEN** the ROI ladder ORDER SHALL change accordingly and saving a scenario SHALL add it to the recent list within the UI

#### Scenario: API Contract Validation For deals/rank
- **WHEN** contract tests call `/api/deals/rank`
- **THEN** the response SHALL include `ladder` entries with `npv`, `irr`, `payback_mo`, and the ladder SHALL be sorted ascending by `roi_rank`
