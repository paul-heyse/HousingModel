## ADDED Requirements

### Requirement: FastAPI Application Infrastructure
The system SHALL provide a `aker_gui.app:create_app()` application factory that creates a FastAPI application hosting both REST API endpoints and a Dash web interface with proper middleware, authentication, and deployment configuration.

#### Scenario: Application Factory Creates Production-Ready App
- **WHEN** `create_app()` is called with configuration
- **THEN** it SHALL return a FastAPI app with CORS, security headers, and logging middleware
- **AND** it SHALL mount Dash application at `/app` path
- **AND** it SHALL mount REST API at `/api` path
- **AND** it SHALL configure authentication session management
- **AND** it SHALL be deployable with Uvicorn/Gunicorn

#### Scenario: Authentication Stub Provides Session Management
- **WHEN** users access protected routes without authentication
- **THEN** they SHALL be redirected to login page
- **AND** successful login SHALL establish authenticated session
- **AND** session SHALL persist across requests with configurable timeout
- **AND** logout SHALL clear session and redirect appropriately

#### Scenario: Health Check and Metrics Endpoints Available
- **WHEN** health check endpoint is accessed
- **THEN** it SHALL return 200 OK with system status
- **AND** metrics endpoint SHALL provide Prometheus-formatted data
- **AND** both endpoints SHALL be accessible without authentication

### Requirement: REST API Layer
The system SHALL provide comprehensive REST API endpoints for all backend functionality including markets, assets, deals, portfolio, and exports with proper error handling, pagination, and filtering.

#### Scenario: Market API Provides Full CRUD Operations
- **WHEN** `/api/markets/{msa_id}` endpoints are accessed
- **THEN** GET SHALL return market data with pillar scores and risk multipliers
- **AND** POST SHALL create new market analysis
- **AND** PUT SHALL update existing market data
- **AND** DELETE SHALL remove market from analysis (with confirmation)

#### Scenario: Asset API Supports Portfolio Integration
- **WHEN** `/api/assets/*` endpoints are accessed
- **THEN** they SHALL integrate with portfolio exposure calculations
- **AND** provide asset fit scores and guardrail compliance
- **AND** support bulk operations for portfolio analysis
- **AND** include geographic and market context data

#### Scenario: Export API Generates Multiple Formats
- **WHEN** `/api/exports/*` endpoints are accessed
- **THEN** they SHALL generate Excel workbooks with all required sheets
- **AND** create Word documents with proper templates
- **AND** produce PDF reports with charts and data lineage
- **AND** support custom date ranges and filtering

### Requirement: Dash Multi-Page Application
The system SHALL provide a multi-page Dash application with navigation, responsive design, and real-time data updates accessible at `/app` with proper routing and state management.

#### Scenario: Navigation Provides Access to All Dashboards
- **WHEN** users navigate through the application
- **THEN** sidebar navigation SHALL provide access to all 7 dashboard pages
- **AND** breadcrumb navigation SHALL show current location
- **AND** URL routing SHALL update browser history
- **AND** page state SHALL persist during navigation

#### Scenario: Responsive Design Works on All Devices
- **WHEN** application is accessed on different screen sizes
- **THEN** layout SHALL adapt responsively to mobile, tablet, and desktop
- **AND** touch interactions SHALL work on mobile devices
- **AND** charts and tables SHALL be readable on small screens
- **AND** navigation SHALL collapse to hamburger menu on mobile

### Requirement: Market Scorecard Dashboard
The system SHALL provide an interactive Market Scorecard dashboard with map visualization, pillar score cards, data vintage indicators, and export functionality.

#### Scenario: Interactive Map Shows Market Boundaries and Scores
- **WHEN** Market Scorecard page loads
- **THEN** it SHALL display an interactive map with MSA boundaries
- **AND** color-coded markers SHALL indicate pillar scores (0-5 scale)
- **AND** clicking markers SHALL show detailed market information
- **AND** zoom and pan controls SHALL allow navigation
- **AND** legend SHALL explain color coding

#### Scenario: Pillar Score Cards Display Normalized Metrics
- **WHEN** viewing market details
- **THEN** four pillar cards SHALL show Supply, Jobs, Urban, Outdoors scores
- **AND** each card SHALL display normalized 0-100 values and 0-5 buckets
- **AND** hover tooltips SHALL show underlying metrics
- **AND** cards SHALL update when market selection changes

#### Scenario: Data Vintage Banner Shows Freshness
- **WHEN** viewing any market data
- **THEN** data vintage banner SHALL show last update timestamp
- **AND** color coding SHALL indicate data age (green=fresh, yellow=stale, red=expired)
- **AND** refresh button SHALL trigger data update
- **AND** vintage SHALL be included in all exports

### Requirement: Deal Workspace Dashboard
The system SHALL provide a Deal Workspace dashboard with archetype selection, scope templates, ROI analysis, and downtime scheduling capabilities.

#### Scenario: Archetype Selection Guides Deal Configuration
- **WHEN** creating or editing a deal
- **THEN** archetype selector SHALL provide options (Classic value-add, Heavy lift, Town-center infill)
- **AND** selection SHALL pre-populate scope templates and assumptions
- **AND** custom archetype creation SHALL be supported
- **AND** archetype SHALL influence all downstream calculations

#### Scenario: Scope Template Library Provides Standardized Options
- **WHEN** configuring deal scope
- **THEN** template library SHALL show light/medium/heavy renovation options
- **AND** each template SHALL include cost/door, expected lift, downtime estimates
- **AND** ROI ladder SHALL rank templates by payback period
- **AND** custom scopes SHALL be savable as new templates

#### Scenario: Downtime Schedule Visualization Shows Impact
- **WHEN** viewing deal timeline
- **THEN** Gantt-style chart SHALL show renovation phases and downtime
- **AND** occupancy impact SHALL be visualized
- **AND** schedule SHALL be editable with drag-and-drop
- **AND** critical path SHALL be highlighted

### Requirement: Asset Fit Wizard Dashboard
The system SHALL provide a guided Asset Fit Wizard with step-by-step checklist, live scoring, and guardrail compliance checking.

#### Scenario: Step-by-Step Guided Configuration Process
- **WHEN** creating asset evaluation
- **THEN** wizard SHALL guide through product type, vintage, unit mix steps
- **AND** progress indicator SHALL show completion status
- **AND** back/forward navigation SHALL preserve state
- **AND** validation SHALL prevent incomplete submissions

#### Scenario: Live Fit Score Updates During Configuration
- **WHEN** adjusting asset parameters
- **THEN** fit score SHALL update in real-time (0-100 scale)
- **AND** score breakdown SHALL show contributing factors
- **AND** color coding SHALL indicate fit quality (red=poor, yellow=moderate, green=excellent)
- **AND** score SHALL include market context weighting

#### Scenario: Guardrail Compliance Flags Violations
- **WHEN** asset configuration violates guardrails
- **THEN** violation flags SHALL be displayed with severity levels
- **AND** specific violated rules SHALL be listed with explanations
- **AND** suggested corrections SHALL be provided
- **AND** override capability SHALL exist for justified exceptions

### Requirement: Risk Panel Dashboard
The system SHALL provide a Risk Panel dashboard with hazard mapping, insurance scenario modeling, and risk multiplier visualization.

#### Scenario: Hazard Map Overlays Show Geographic Risks
- **WHEN** viewing Risk Panel
- **THEN** map SHALL display WUI, hail, snow load, and flood zones
- **AND** overlay toggles SHALL allow selective risk visualization
- **AND** risk severity SHALL be color-coded
- **AND** clicking locations SHALL show detailed risk factors

#### Scenario: Insurance Scenario Modeling Calculates Premiums
- **WHEN** adjusting insurance parameters
- **THEN** scenario modeling SHALL calculate premium impacts
- **AND** deductible variations SHALL be modeled
- **AND** coverage option comparisons SHALL be available
- **AND** results SHALL include confidence intervals

#### Scenario: Risk Multiplier Visualization Shows Impact
- **WHEN** viewing risk analysis
- **THEN** multiplier effects on cap rates and contingencies SHALL be shown
- **AND** waterfall charts SHALL break down multiplier components
- **AND** sensitivity analysis SHALL show multiplier ranges
- **AND** state-specific patterns SHALL be highlighted

### Requirement: Ops & Brand Dashboard
The system SHALL provide an Ops & Brand dashboard with NPS tracking, reputation management, and operational KPI monitoring.

#### Scenario: NPS and Review Ingestion Interface
- **WHEN** accessing Ops & Brand dashboard
- **THEN** NPS score trends SHALL be displayed with historical data
- **AND** review ingestion interface SHALL allow manual entry
- **AND** sentiment analysis SHALL categorize reviews
- **AND** response tracking SHALL monitor management replies

#### Scenario: Reputation Index Tracks Brand Performance
- **WHEN** viewing reputation metrics
- **THEN** composite reputation index SHALL combine multiple factors
- **AND** trend analysis SHALL show improvement/decline patterns
- **AND** benchmarking SHALL compare to market standards
- **AND** alerts SHALL trigger on significant changes

#### Scenario: Pricing Rule Configuration and Testing
- **WHEN** configuring pricing rules
- **THEN** reputation→pricing relationship SHALL be configurable
- **AND** rule testing interface SHALL simulate scenarios
- **AND** impact analysis SHALL show revenue effects
- **AND** A/B testing framework SHALL support rule validation

### Requirement: Data Refresh Dashboard
The system SHALL provide a Data Refresh dashboard with source management, run logs, lineage tracking, and manual refresh capabilities.

#### Scenario: Data Source Toggle Interface
- **WHEN** managing data sources
- **THEN** toggle interface SHALL enable/disable sources by category
- **AND** refresh frequency SHALL be configurable per source
- **AND** source status SHALL show last successful/failed run
- **AND** dependency relationships SHALL be visualized

#### Scenario: Last-Run Logs and Status Indicators
- **WHEN** viewing data operations
- **THEN** chronological log SHALL show all refresh activities
- **AND** status indicators SHALL use color coding (green=success, red=failure)
- **AND** drill-down SHALL show detailed error messages
- **AND** retry functionality SHALL be available for failed runs

#### Scenario: Lineage Drill-Down Visualization
- **WHEN** exploring data lineage
- **THEN** interactive graph SHALL show data flow from sources to outputs
- **AND** node details SHALL include transformation logic
- **AND** dependency chains SHALL be traceable
- **AND** impact analysis SHALL show downstream effects of failures

### Requirement: CO/UT/ID Patterning Dashboard
The system SHALL provide a CO/UT/ID Patterning dashboard with state-specific configurations, hazard pattern visualization, and regional comparison tools.

#### Scenario: State-Specific Default Configuration
- **WHEN** selecting state (CO/UT/ID)
- **THEN** default configurations SHALL auto-populate appropriate settings
- **AND** hazard patterns SHALL be pre-selected based on state
- **AND** regulatory rules SHALL be applied automatically
- **AND** override controls SHALL allow customization

#### Scenario: Hazard Pattern Visualization
- **WHEN** viewing state patterns
- **THEN** hazard maps SHALL show state-specific risk patterns
- **AND** pattern overlays SHALL highlight regional variations
- **AND** temporal analysis SHALL show seasonal patterns
- **AND** comparison tools SHALL benchmark across states

#### Scenario: Regional Comparison Tools
- **WHEN** comparing regions
- **THEN** side-by-side comparison SHALL show metric differences
- **AND** normalized scoring SHALL account for regional variations
- **AND** pattern identification SHALL highlight similarities/differences
- **AND** export functionality SHALL include regional analysis

### Requirement: Real-Time Data Integration
The system SHALL provide real-time data updates via WebSocket connections, cross-dashboard data sharing, and unified search capabilities.

#### Scenario: WebSocket Real-Time Updates
- **WHEN** background data updates occur
- **THEN** connected dashboards SHALL receive real-time updates
- **AND** update indicators SHALL show data freshness
- **AND** conflict resolution SHALL handle concurrent updates
- **AND** offline mode SHALL queue updates for reconnection

#### Scenario: Cross-Dashboard Data Sharing
- **WHEN** data is modified in one dashboard
- **THEN** related dashboards SHALL reflect changes immediately
- **AND** shared state SHALL be consistent across all views
- **AND** user actions SHALL propagate to relevant dashboards
- **AND** conflict resolution SHALL prevent data corruption

#### Scenario: Unified Search and Filtering
- **WHEN** searching across the application
- **THEN** unified search SHALL find markets, assets, deals, and portfolio items
- **AND** advanced filters SHALL support complex queries
- **AND** search results SHALL be ranked by relevance
- **AND** saved searches SHALL be shareable across users
