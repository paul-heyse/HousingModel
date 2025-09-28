# GUI Specification

## Purpose
Provide a user-friendly web interface for the Aker Property Model using Dash/Plotly for analysts and stakeholders to interact with market analysis, asset evaluation, and deal management without requiring programming knowledge.
## Requirements
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

### Requirement: Ops & Brand Dashboard
The system SHALL provide a comprehensive Ops & Brand dashboard for monitoring reputation metrics, managing review data uploads, and configuring reputation-driven pricing guardrails.

#### Scenario: Dashboard Navigation and Access
- **GIVEN** an operations user accessing the application
- **WHEN** navigating to `/app/ops?asset_id=AKR-123`
- **THEN** the system SHALL display the Ops & Brand dashboard
- **AND** show breadcrumb navigation "Ops & Brand"
- **AND** load asset-specific data for AKR-123
- **AND** initialize with default 12-month date range

#### Scenario: Reputation Data Retrieval
- **GIVEN** an asset with reputation data
- **WHEN** the dashboard loads
- **THEN** the system SHALL call `GET /api/ops/reputation?asset_id=AKR-123`
- **AND** return reputation index (0-100), NPS time series, review volume/rating data
- **AND** include current pricing rules based on reputation index
- **AND** display data in appropriate chart formats

#### Scenario: CSV Review Upload Processing
- **GIVEN** a user with Analyst role uploading a CSV file
- **WHEN** `POST /api/ops/reviews/upload` is called with multipart CSV data
- **THEN** the system SHALL validate CSV schema (date, source, rating, text, response_time_days, is_move_in)
- **AND** process valid rows and update reputation metrics
- **AND** return ingestion summary with counts and sample errors
- **AND** refresh dashboard charts with new data

#### Scenario: Pricing Guardrail Preview
- **GIVEN** a reputation index value
- **WHEN** `GET /api/ops/pricing/preview?asset_id=AKR-123&reputation_idx=78` is called
- **THEN** the system SHALL return preview of pricing guardrails
- **AND** include max concession days, floor price percentage, and premium cap percentage
- **AND** update the pricing rules table in real-time
- **AND** support what-if scenario modeling

#### Scenario: Interactive Chart Display
- **GIVEN** loaded reputation and review data
- **WHEN** the dashboard renders
- **THEN** the system SHALL display NPS trend line chart in left column
- **AND** show dual-axis chart with review volume (bars) and average rating (line)
- **AND** render reputation index gauge with color-coded ranges (Poor/Fair/Good/Excellent)
- **AND** display pricing rules table with current guardrail settings

#### Scenario: What-If Scenario Modeling
- **GIVEN** a reputation index slider in the dashboard
- **WHEN** the slider value is adjusted
- **THEN** the system SHALL call `/api/ops/pricing/preview` with new index value
- **AND** update pricing rules table without persisting changes
- **AND** maintain current operational settings while showing preview
- **AND** revert to actual values when slider is reset

#### Scenario: Data State Management
- **GIVEN** dashboard with time range and source filters
- **WHEN** filters are applied
- **THEN** the system SHALL store filter state in URL query parameters
- **AND** maintain filter state across page refreshes
- **AND** cache upload results in dcc.Store until navigation
- **AND** persist dashboard preferences in localStorage

#### Scenario: Error and Empty State Handling
- **GIVEN** an asset with no historical reputation data
- **WHEN** the dashboard loads
- **THEN** charts SHALL display "No data for selected range" messaging
- **AND** provide upload CSV hint and template download link
- **AND** maintain functional interface for data entry
- **AND** show helpful onboarding guidance

#### Scenario: CSV Validation and Error Reporting
- **GIVEN** a CSV upload with validation errors
- **WHEN** processing the uploaded file
- **THEN** the system SHALL validate each row against required schema
- **AND** return detailed error messages with row numbers
- **AND** display sample errors in expandable error table
- **AND** show ingestion summary with accepted/rejected counts
- **AND** allow partial uploads with error reporting

#### Scenario: Role-Based Access Control
- **GIVEN** a user with Viewer role
- **WHEN** attempting CSV upload
- **THEN** the system SHALL disable upload button
- **AND** display tooltip "Upload requires Analyst role"
- **AND** allow viewing of existing data and charts
- **AND** prevent data modification operations

#### Scenario: Telemetry and Analytics
- **GIVEN** dashboard user interactions
- **WHEN** users upload CSV files or adjust filters
- **THEN** the system SHALL log anonymized telemetry events
- **AND** track upload attempt counts and rejection rates
- **AND** monitor dashboard usage patterns
- **AND** exclude review text content from logging

#### Scenario: End-to-End Workflow Testing
- **GIVEN** a complete dashboard workflow
- **WHEN** Playwright tests execute
- **THEN** uploading template CSV SHALL increase review counts
- **AND** adjust reputation index calculations
- **AND** update pricing guardrails display
- **AND** validate CSV schema requirements
- **AND** test role-based permission enforcement

#### Scenario: API Contract Validation
- **GIVEN** API endpoints for reputation and pricing data
- **WHEN** endpoints are called
- **THEN** reputation endpoint SHALL return numeric index ∈ [0,100]
- **AND** include required time series data structures
- **AND** pricing preview SHALL return valid guardrail configurations
- **AND** CSV upload SHALL return structured validation results
- **AND** maintain consistent API response formats

