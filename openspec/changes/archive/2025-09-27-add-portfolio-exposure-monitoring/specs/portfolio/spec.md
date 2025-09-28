## ADDED Requirements

### Requirement: Portfolio Exposure Computation Engine
The system SHALL provide a `portfolio.compute_exposures(positions)` function that calculates exposure concentrations across multiple dimensions including strategy, state, MSA, submarket, vintage, construction type, and rent band with real-time aggregation and threshold monitoring.

#### Scenario: Multi-Dimensional Exposure Calculation
- **WHEN** `portfolio.compute_exposures(positions)` is called with a list of portfolio positions
- **THEN** it SHALL calculate exposure percentages for each dimension (strategy, state, MSA, etc.)
- **AND** it SHALL aggregate exposures by combining position values within each dimension
- **AND** it SHALL persist the results to `portfolio_exposures` table with timestamp and run metadata

#### Scenario: Geographic Exposure Analysis
- **WHEN** computing exposures with geographic dimensions (MSA, submarket)
- **THEN** it SHALL integrate with existing market and geographic data
- **AND** it SHALL calculate geographic concentration metrics
- **AND** it SHALL flag geographic concentrations exceeding configured thresholds

#### Scenario: Real-Time Exposure Updates
- **WHEN** portfolio positions are updated via API or data import
- **THEN** exposure calculations SHALL trigger automatically
- **AND** updated exposures SHALL be persisted immediately
- **AND** relevant alerts SHALL be generated for threshold breaches

### Requirement: Configurable Exposure Thresholds
The system SHALL support configurable exposure thresholds by dimension with severity levels and automated alert generation when thresholds are breached.

#### Scenario: Threshold Configuration Management
- **WHEN** portfolio managers configure exposure limits via dashboard or API
- **THEN** thresholds SHALL be persisted to `exposure_thresholds` table
- **AND** thresholds SHALL be applied across all exposure calculations
- **AND** threshold changes SHALL trigger immediate re-evaluation of existing exposures

#### Scenario: Alert Generation and Notification
- **WHEN** exposure calculations detect threshold breaches
- **THEN** alerts SHALL be created in `portfolio_alerts` table
- **AND** notifications SHALL be sent via configured channels (email, dashboard, API)
- **AND** alert severity SHALL be calculated based on breach magnitude and threshold type

#### Scenario: Alert Acknowledgment and Resolution
- **WHEN** portfolio managers acknowledge alerts via dashboard
- **THEN** alert status SHALL be updated to acknowledged
- **AND** alert history SHALL be maintained for audit purposes
- **AND** resolution tracking SHALL support compliance reporting

### Requirement: Exposure Dashboard Integration
The system SHALL provide dashboard-ready exposure aggregates with real-time visualization components including exposure dials, trend charts, and drill-down capabilities.

#### Scenario: Exposure Dashboard Components
- **WHEN** users access the portfolio dashboard
- **THEN** exposure dials SHALL display current concentrations by key dimensions
- **AND** trend charts SHALL show exposure changes over time
- **AND** drill-down SHALL allow detailed analysis by specific dimensions

#### Scenario: Real-Time Dashboard Updates
- **WHEN** exposure calculations complete
- **THEN** dashboard components SHALL update automatically
- **AND** WebSocket connections SHALL push updates to active dashboard sessions
- **AND** cached exposure data SHALL be invalidated and refreshed

### Requirement: Portfolio Position Data Integration
The system SHALL integrate with existing asset and market data to enrich exposure calculations with geographic, market, and asset-specific context.

#### Scenario: Asset Data Enrichment
- **WHEN** processing portfolio positions
- **THEN** position data SHALL be enriched with asset details (vintage, construction type, etc.)
- **AND** geographic data SHALL be integrated for MSA/submarket analysis
- **AND** market scores SHALL be included for risk-weighted exposure calculations

#### Scenario: Position Import and Validation
- **WHEN** portfolio positions are imported via API or file upload
- **THEN** positions SHALL be validated against asset database
- **AND** missing or invalid positions SHALL be flagged with clear error messages
- **AND** import history SHALL be maintained for audit purposes
