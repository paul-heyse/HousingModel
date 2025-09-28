## ADDED Requirements
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
