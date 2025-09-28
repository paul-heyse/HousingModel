## MODIFIED Requirements
### Requirement: Asset Fit Wizard Dashboard
The system SHALL provide a guided Asset Fit Wizard with step-by-step checklist, live scoring, and guardrail compliance checking. The wizard SHALL be available at `/app/asset-fit` and accept query parameters (`asset_id`, `msa_id`) so links from Deal Workspace remain deep-linkable.

#### Scenario: Step-by-Step Guided Configuration Process
- **WHEN** analysts open `/app/asset-fit?asset_id=AKR-123&msa_id=BOI`
- **THEN** the UI SHALL render a breadcrumb `Assets → Fit Wizard`, stepper stages `Product → Units → Physical → Parking & Transit → Amenities → Summary`, and highlight the active step
- **AND** navigation controls (Previous/Next, Reset to product standards) SHALL preserve entered values while moving between steps
- **AND** product defaults fetched from the mandate SHALL populate when “Reset to product standards” is clicked
- **AND** missing required context (e.g., unit counts) SHALL mark the relevant step with a red status indicator and display “Required to compute Fit Score” copy

#### Scenario: Live Fit Score Updates During Configuration
- **WHEN** inputs change on any step
- **THEN** the client SHALL debounce changes (≤400 ms) and POST to `/api/assets/fit` with `{asset_id, inputs{…}}`
- **AND** the response (`fit_score ∈ [0,100]`, `flags[]`, `observed/target`) SHALL update the score gauge, summary copy, and flag listings without losing input focus
- **AND** input changes SHALL set an “Unsaved changes” pill until a successful POST response is received
- **AND** auto-save SHALL cache the current state per `asset_id` via `localStorage` so reloads restore the wizard

#### Scenario: Guardrail Compliance Flags and Interactions
- **WHEN** guardrail flags are returned (`severity: info|warn|fail`)
- **THEN** the right panel SHALL list chips colored by severity and show tooltip details containing rule text, observed value, and target
- **AND** selecting a flag SHALL scroll to and briefly highlight the related control
- **AND** clicking “Save report” SHALL be available only to roles with Analyst/Admin privileges and persist the evaluation via the existing fit report workflow

#### Scenario: API and Mandate Dependencies
- **WHEN** the wizard initializes
- **THEN** it SHALL load asset context via `GET /api/assets/{asset_id}` and guardrail mandate thresholds via `GET /api/mandate/guardrails`
- **AND** failure to load guardrails SHALL display a blocking banner “Unable to load guardrails; Fit Score disabled” with retry capability and disable the POST fit call
- **AND** the API contract SHALL guarantee that `POST /api/assets/fit` returns `score`, `flags[{code,severity,message,observed,target}]`, and `fit_report_id` when persisted

#### Scenario: Telemetry and Security Controls
- **WHEN** users trigger flag changes or save reports
- **THEN** telemetry events SHALL record anonymized counts of flag codes for product standards tuning
- **AND** attempts by Viewer-role users to persist a report SHALL return HTTP 403 and the UI SHALL show a permission tooltip while still allowing on-screen calculations

#### Scenario: Tests and Definition of Done
- **WHEN** the change is delivered
- **THEN** Playwright regression SHALL verify toggling “In-unit W/D” flips a fail→pass flag and updates the score text
- **AND** contract tests SHALL assert `POST /api/assets/fit` bounds and flag payload completeness
- **AND** a snapshot fixture asset SHALL produce an identical Fit Score across tagged releases to guard against calculation drift
