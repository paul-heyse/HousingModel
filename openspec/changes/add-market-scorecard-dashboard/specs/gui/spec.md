## ADDED Requirements

### Requirement: Interactive Map Component with MSA Visualization
The Market Scorecard dashboard SHALL provide an interactive map component using dash-leaflet that displays MSA boundaries with color-coded pillar scores and supports zoom, pan, and selection interactions.

#### Scenario: Map Displays MSA Boundaries with Score Visualization
- **WHEN** the Market Scorecard page loads
- **THEN** an interactive map SHALL display with MSA boundary polygons
- **AND** MSA boundaries SHALL be colored according to overall market scores (0-5 scale)
- **AND** color legend SHALL show score ranges (red=poor, yellow=moderate, green=excellent)
- **AND** map SHALL support zoom and pan controls for navigation

#### Scenario: MSA Selection Updates Map and Cards
- **WHEN** a user clicks on an MSA boundary
- **THEN** the MSA SHALL be highlighted on the map
- **AND** pillar score cards SHALL update to show the selected MSA's scores
- **AND** map center SHALL optionally zoom to the selected MSA
- **AND** selection SHALL persist in URL for bookmarking

#### Scenario: Map Layers Support Multiple Data Views
- **WHEN** viewing the map interface
- **THEN** layer toggles SHALL allow switching between different data views
- **AND** pillar-specific overlays SHALL show individual metric distributions
- **AND** risk multiplier overlays SHALL display geographic risk factors
- **AND** data vintage indicators SHALL show when data was last updated

### Requirement: Pillar Score Cards with Real-Time Data Binding
The Market Scorecard dashboard SHALL display four pillar score cards (Supply, Jobs, Urban, Outdoors) with real-time data binding from API endpoints and drill-down capabilities.

#### Scenario: Pillar Cards Display Normalized Scores
- **WHEN** viewing market details
- **THEN** four pillar cards SHALL display Supply, Jobs, Urban, and Outdoors scores
- **AND** each card SHALL show both 0-100 normalized values and 0-5 bucket scores
- **AND** cards SHALL update in real-time when MSA selection changes
- **AND** loading states SHALL indicate when data is being fetched

#### Scenario: Score Cards Include Trend Indicators
- **WHEN** viewing pillar score cards
- **THEN** trend arrows SHALL indicate score changes over time
- **AND** color coding SHALL show improvement (green) or decline (red)
- **AND** hover tooltips SHALL show historical values and change percentages
- **AND** trend period SHALL be configurable (1M, 3M, 1Y)

#### Scenario: Drill-Down Provides Detailed Metrics
- **WHEN** clicking on a pillar score card
- **THEN** detailed metrics breakdown SHALL be displayed
- **AND** underlying data points SHALL be shown with their contributions
- **AND** data vintage and source attribution SHALL be visible
- **AND** export options SHALL be available for detailed views

### Requirement: Data Vintage Banner with Refresh Controls
The Market Scorecard dashboard SHALL display a data vintage banner with freshness indicators, last update timestamps, and manual refresh capabilities.

#### Scenario: Data Vintage Banner Shows Freshness Status
- **WHEN** viewing any market data
- **THEN** a banner SHALL display data vintage and last update timestamp
- **AND** color coding SHALL indicate data age (green=fresh, yellow=stale, red=expired)
- **AND** source attribution SHALL show which APIs provided the data
- **AND** banner SHALL be visible on all Market Scorecard views

#### Scenario: Manual Refresh Triggers Data Updates
- **WHEN** clicking the refresh button
- **THEN** a loading indicator SHALL appear
- **AND** API calls SHALL be made to refresh market data
- **AND** success/failure notifications SHALL be displayed
- **AND** data vintage timestamps SHALL update on successful refresh

#### Scenario: Automatic Refresh Scheduling
- **WHEN** the dashboard is active
- **THEN** data SHALL refresh automatically based on configurable intervals
- **AND** background refresh SHALL not interrupt user interactions
- **AND** refresh failures SHALL trigger user notifications
- **AND** refresh scheduling SHALL be configurable per data source

### Requirement: Export Functionality for Reports
The Market Scorecard dashboard SHALL provide export functionality for generating Excel workbooks, Word documents, and PDF reports with current view data and visualizations.

#### Scenario: Excel Export Includes All Market Data
- **WHEN** clicking the Excel export button
- **THEN** an Excel workbook SHALL be generated with multiple sheets
- **AND** sheets SHALL include Overview, Market Scores, Detailed Metrics, and Data Lineage
- **AND** formatting SHALL match existing report templates
- **AND** download SHALL start automatically with progress indication

#### Scenario: Word Export Creates Investment Memo
- **WHEN** clicking the Word export button
- **THEN** a Word document SHALL be generated using existing templates
- **AND** document SHALL include selected market analysis and charts
- **AND** formatting SHALL follow IC-ready investment memo standards
- **AND** charts SHALL be embedded as high-quality images

#### Scenario: PDF Export Generates Professional Report
- **WHEN** clicking the PDF export button
- **THEN** a PDF report SHALL be generated with professional formatting
- **AND** report SHALL include map screenshots and score visualizations
- **AND** data lineage and methodology SHALL be included in appendix
- **AND** report SHALL be optimized for printing and sharing

### Requirement: MSA Selection and Filtering Interface
The Market Scorecard dashboard SHALL provide comprehensive MSA selection and filtering capabilities with search, multi-select, and geographic filtering options.

#### Scenario: MSA Selector Provides Search and Selection
- **WHEN** using the MSA selector
- **THEN** dropdown SHALL support text search by MSA name or ID
- **AND** multi-select SHALL allow comparison of multiple markets
- **AND** recently viewed MSAs SHALL appear in quick-select list
- **AND** selection SHALL update map highlighting and score cards

#### Scenario: Geographic Filters Enable Regional Analysis
- **WHEN** using geographic filters
- **THEN** state and region filters SHALL be available
- **AND** custom boundary selection SHALL be supported
- **AND** filter combinations SHALL work together
- **AND** filtered results SHALL update map and cards immediately

#### Scenario: Score-Based Filtering and Sorting
- **WHEN** using score filters
- **THEN** minimum/maximum score ranges SHALL be configurable per pillar
- **AND** sorting options SHALL be available (score, name, state, etc.)
- **AND** filter state SHALL persist in URL for bookmarking
- **AND** bulk operations SHALL be available for filtered results

### Requirement: Real-Time Data Integration
The Market Scorecard dashboard SHALL integrate with real-time data sources and provide live updates without requiring page refreshes.

#### Scenario: WebSocket Updates Provide Real-Time Data
- **WHEN** market data is updated in the background
- **THEN** connected dashboards SHALL receive real-time updates via WebSocket
- **AND** update indicators SHALL show data freshness changes
- **AND** only relevant components SHALL update (no full page refresh)
- **AND** connection status SHALL be visible to users

#### Scenario: API Integration Provides Current Data
- **WHEN** loading market data
- **THEN** API calls SHALL fetch current pillar scores and metrics
- **AND** data SHALL be validated and sanitized before display
- **AND** loading states SHALL provide user feedback
- **AND** error states SHALL offer retry options

#### Scenario: Cross-Component Data Synchronization
- **WHEN** data changes in one component
- **THEN** related components SHALL update automatically
- **AND** state SHALL be shared between map, cards, and filters
- **AND** user selections SHALL propagate across all components
- **AND** conflicting updates SHALL be resolved gracefully
