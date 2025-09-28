## ADDED Requirements

### Requirement: Risk Panel Dashboard Navigation and Routing
The Risk Panel dashboard SHALL provide comprehensive navigation with URL parameter support for scope-based analysis and breadcrumb navigation for user orientation.

#### Scenario: URL Parameters Control Dashboard Scope
- **WHEN** users navigate to `/app/risk?scope=market&msa_id=BOI`
- **THEN** dashboard SHALL load market-specific risk analysis for Boise MSA
- **AND** scope selector SHALL show "Market" as active
- **AND** MSA selector SHALL be populated with BOI as default
- **AND** breadcrumb SHALL show "Risk & Resilience > Market Analysis"

#### Scenario: Asset Scope Navigation Works Similarly
- **WHEN** users navigate to `/app/risk?scope=asset&asset_id=AKR-123`
- **THEN** dashboard SHALL load asset-specific risk analysis for AKR-123
- **AND** scope selector SHALL show "Asset" as active
- **AND** asset selector SHALL be populated with AKR-123 as default
- **AND** breadcrumb SHALL show "Risk & Resilience > Asset Analysis"

#### Scenario: Scope Switching Preserves Context
- **WHEN** users switch from market to asset scope
- **THEN** URL parameters SHALL update to reflect new scope
- **AND** appropriate selectors SHALL be enabled/disabled
- **AND** risk data SHALL reload for the new scope
- **AND** user selections SHALL be preserved where applicable

### Requirement: Interactive Map with Peril Overlays
The Risk Panel dashboard SHALL provide an interactive map with peril-specific overlays, layer toggles, and location-based information display.

#### Scenario: Peril Overlays Display Geographic Risk Data
- **WHEN** users select peril checkboxes in the sidebar
- **THEN** corresponding map overlays SHALL be displayed
- **AND** overlays SHALL use color-coded severity scales (0-100 index)
- **AND** legend SHALL update to show active peril color mappings
- **AND** layer opacity SHALL be configurable for multiple overlays

#### Scenario: Map Interactions Provide Location-Specific Data
- **WHEN** users click on map locations
- **THEN** popup SHALL display peril values for that location
- **AND** popup SHALL show specific metrics (WUI class, hail frequency, etc.)
- **AND** popup SHALL include severity indices and risk multipliers
- **AND** popup data SHALL be contextually relevant to selected perils

#### Scenario: Layer Controls Enable Selective Visualization
- **WHEN** users interact with layer toggle controls
- **THEN** individual peril layers SHALL be showable/hideable
- **AND** layer order SHALL be controllable for overlay stacking
- **AND** base map SHALL remain visible when peril layers are toggled
- **AND** layer state SHALL persist in user session

### Requirement: Risk Profile Data API Integration
The Risk Panel dashboard SHALL integrate with risk profile APIs to provide comprehensive peril data with proper error handling and data validation.

#### Scenario: Risk Profile API Returns Structured Peril Data
- **WHEN** `/api/risk/profile` endpoint is called with scope and ID
- **THEN** response SHALL include array of peril objects with required fields
- **AND** each peril SHALL have severity_idx (0-100), insurance_deductible, and multiplier
- **AND** response SHALL be validated against peril profile schema
- **AND** API SHALL handle both market and asset scope parameters

#### Scenario: Peril Overlays API Provides Geographic Data
- **WHEN** `/api/risk/overlays` endpoint is called with MSA ID
- **THEN** response SHALL provide GeoJSON or vector tile data for each peril
- **AND** data SHALL include severity indices and risk classifications
- **AND** response SHALL support efficient map rendering
- **AND** API SHALL handle missing data gracefully

#### Scenario: Insurance Scenario API Models Risk Adjustments
- **WHEN** `/api/insurance/scenario` endpoint receives scenario configuration
- **THEN** response SHALL include multipliers_table with base and scenario multipliers
- **AND** response SHALL include exit_cap_bps_delta and contingency_pct_delta
- **AND** scenario calculations SHALL be deterministic and auditable
- **AND** API SHALL validate input parameters and return appropriate errors

### Requirement: Insurance Scenario Configuration Interface
The Risk Panel dashboard SHALL provide comprehensive insurance scenario configuration with deductible options, parametric coverage, and real-time impact calculation.

#### Scenario: Deductible Configuration Interface
- **WHEN** users access the scenario configuration panel
- **THEN** deductible dropdowns SHALL be available for each peril type
- **AND** options SHALL include standard values ($10k, $25k, $50k, $100k, etc.)
- **AND** custom deductible input SHALL be supported
- **AND** selections SHALL update multiplier calculations in real-time

#### Scenario: Parametric Insurance Options
- **WHEN** users configure parametric coverage
- **THEN** checkboxes SHALL be available for parametric triggers
- **AND** options SHALL include wind speed, precipitation, temperature thresholds
- **AND** parametric parameters SHALL be configurable per peril
- **AND** selections SHALL affect scenario multiplier calculations

#### Scenario: Scenario Application and Impact Display
- **WHEN** users click "Apply scenario"
- **THEN** API call SHALL be made to calculate scenario impacts
- **AND** multipliers table SHALL update with new values
- **AND** impact summary cards SHALL refresh with updated deltas
- **AND** export preview SHALL update to reflect changes

### Requirement: Multipliers Table with Comparative Analysis
The Risk Panel dashboard SHALL display a comprehensive multipliers table showing base multipliers, scenario adjustments, and impact deltas with sorting and filtering capabilities.

#### Scenario: Multipliers Table Displays All Peril Data
- **WHEN** viewing the multipliers table
- **THEN** table SHALL show all available perils with their data
- **AND** columns SHALL include Peril, Severity Index, Base Multiplier, Scenario Multiplier, Δ
- **AND** rows SHALL be color-coded by severity level
- **AND** table SHALL support sorting by any column

#### Scenario: Table Filtering Works with Peril Selection
- **WHEN** users select/deselect perils in sidebar
- **THEN** table SHALL filter to show only selected perils
- **AND** totals SHALL recalculate based on filtered perils
- **AND** impact calculations SHALL update for filtered view
- **AND** filter state SHALL persist in user session

#### Scenario: Impact Calculations Update in Real-Time
- **WHEN** scenario parameters change
- **THEN** scenario multipliers SHALL update immediately
- **AND** delta calculations SHALL refresh automatically
- **AND** impact summary SHALL update with new values
- **AND** all dependent visualizations SHALL refresh

### Requirement: Impact Summary Cards
The Risk Panel dashboard SHALL provide impact summary cards showing the aggregate effects of risk scenarios on exit cap rates and contingency requirements.

#### Scenario: Exit Cap Impact Display
- **WHEN** viewing impact summary
- **THEN** exit cap impact card SHALL show basis point delta
- **AND** card SHALL use color coding (green for positive, red for negative impact)
- **AND** card SHALL show both absolute and percentage changes
- **AND** card SHALL update in real-time as scenarios change

#### Scenario: Contingency Impact Display
- **WHEN** viewing impact summary
- **THEN** contingency impact card SHALL show percentage delta
- **AND** card SHALL use color coding for impact direction
- **AND** card SHALL show both absolute and percentage changes
- **AND** card SHALL update in real-time as scenarios change

#### Scenario: Impact Breakdown Provides Detail
- **WHEN** users interact with impact cards
- **THEN** detailed breakdown SHALL show contribution by peril
- **AND** breakdown SHALL include base vs scenario comparisons
- **AND** breakdown SHALL support drill-down to specific metrics
- **AND** breakdown data SHALL be exportable

### Requirement: Export Preview Integration
The Risk Panel dashboard SHALL provide an integrated export preview that shows how risk analysis will appear in generated reports with real-time updates.

#### Scenario: Export Preview Shows Risk Section
- **WHEN** viewing the export preview
- **THEN** preview SHALL show risk analysis section as it will appear in PDF
- **AND** preview SHALL include map screenshots and peril data
- **AND** preview SHALL update as scenario parameters change
- **AND** preview SHALL be scrollable and zoomable

#### Scenario: Preview Controls Enable Customization
- **WHEN** interacting with preview controls
- **THEN** zoom controls SHALL allow detailed viewing
- **AND** format selection SHALL preview different report styles
- **AND** section toggles SHALL show/hide specific content
- **AND** preview SHALL maintain aspect ratio for report accuracy

#### Scenario: Preview Integration with Export System
- **WHEN** users initiate export from preview
- **THEN** current preview state SHALL be used for report generation
- **AND** export progress SHALL be displayed
- **AND** download links SHALL be provided on completion
- **AND** preview state SHALL be preserved during export

### Requirement: State Management and Caching
The Risk Panel dashboard SHALL implement comprehensive state management with aggressive caching for overlay tiles and persistent user preferences.

#### Scenario: Overlay Tiles Cached with ETags
- **WHEN** map tiles are requested
- **THEN** requests SHALL include ETag headers for cache validation
- **AND** server SHALL return 304 Not Modified for unchanged tiles
- **AND** tiles SHALL be cached for 1 day with proper invalidation
- **AND** cache SHALL be shared across user sessions

#### Scenario: Panel State Persisted Per Scope
- **WHEN** users configure dashboard settings
- **THEN** state SHALL be saved to dcc.Store with scope-specific keys
- **AND** state SHALL persist across page reloads
- **AND** state SHALL be restored when returning to same scope
- **AND** state SHALL be cleared when switching scopes

#### Scenario: User Preferences Maintained
- **WHEN** users customize interface settings
- **THEN** preferences SHALL be saved to user profile
- **AND** preferences SHALL apply across all dashboard sessions
- **AND** preferences SHALL include map settings, table sorting, etc.
- **AND** preferences SHALL be exportable for backup

### Requirement: Error Handling and Empty States
The Risk Panel dashboard SHALL provide comprehensive error handling with user-friendly empty states and actionable error recovery options.

#### Scenario: Peril Overlay Unavailable States
- **WHEN** peril data is unavailable for selected region
- **THEN** legend SHALL show shaded/inactive state for that peril
- **AND** tooltip SHALL explain "No data for this peril at selected vintage"
- **AND** map SHALL not display overlay for unavailable perils
- **AND** table SHALL show "N/A" for unavailable peril data

#### Scenario: Scenario Engine Error Handling
- **WHEN** scenario calculation fails
- **THEN** inline error messages SHALL appear on form controls
- **AND** previous valid values SHALL be preserved
- **AND** error details SHALL be displayed for user understanding
- **AND** retry functionality SHALL be available for transient errors

#### Scenario: API Failure Recovery
- **WHEN** API calls fail
- **THEN** user-friendly error messages SHALL be displayed
- **AND** retry buttons SHALL be provided for failed operations
- **AND** fallback data SHALL be used when available
- **AND** error state SHALL not break overall dashboard functionality

### Requirement: Security and Access Control
The Risk Panel dashboard SHALL implement comprehensive security measures with role-based access control and audit logging for scenario modifications.

#### Scenario: Role-Based Scenario Management
- **WHEN** users attempt to save default scenarios
- **THEN** only Admin users SHALL be able to save fund-wide defaults
- **AND** all users SHALL be able to save scope-specific scenarios
- **AND** permission checks SHALL occur on save operations
- **AND** unauthorized attempts SHALL be logged and rejected

#### Scenario: Audit Logging for Scenario Modifications
- **WHEN** users modify risk scenarios
- **THEN** all changes SHALL be logged with user, timestamp, and details
- **AND** scenario history SHALL be maintained for compliance
- **AND** audit trail SHALL include before/after values
- **AND** audit data SHALL be available for compliance reporting

#### Scenario: Data Access Controls
- **WHEN** users access risk data
- **THEN** access SHALL be controlled based on user permissions
- **AND** sensitive risk data SHALL be filtered appropriately
- **AND** data access SHALL be logged for audit purposes
- **AND** access patterns SHALL be monitored for security

### Requirement: Telemetry and Analytics
The Risk Panel dashboard SHALL implement comprehensive telemetry for usage analytics, performance monitoring, and user experience optimization.

#### Scenario: Peril Usage Analytics
- **WHEN** users interact with peril features
- **THEN** which perils are viewed most frequently SHALL be tracked
- **AND** which perils are adjusted most often SHALL be monitored
- **AND** view duration per peril SHALL be recorded
- **AND** analytics SHALL inform feature prioritization

#### Scenario: Scenario Adjustment Tracking
- **WHEN** users modify scenario parameters
- **THEN** adjustment frequency SHALL be tracked by parameter type
- **AND** common adjustment patterns SHALL be identified
- **AND** adjustment success rates SHALL be monitored
- **AND** analytics SHALL guide scenario interface improvements

#### Scenario: Performance Metrics Collection
- **WHEN** dashboard operations occur
- **THEN** map rendering performance SHALL be tracked
- **AND** API response times SHALL be monitored
- **AND** user interaction latency SHALL be measured
- **AND** performance data SHALL inform optimization efforts
