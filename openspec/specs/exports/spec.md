# exports Specification

## Purpose
TBD - created by archiving change add-excel-workbook-builder. Update Purpose after archive.
## Requirements
### Requirement: Excel Workbook Builder Engine
The system SHALL provide a comprehensive Excel workbook builder that creates a functionally equivalent document to the Python-based product with live data connections and calculated metrics.

#### Scenario: Complete Workbook Generation
- **GIVEN** valid MSA, asset, and as_of parameters
- **WHEN** `exports.to_excel(msa, asset, as_of)` is called
- **THEN** the system SHALL generate a complete Excel workbook with all 10 required sheets
- **AND** the workbook SHALL open successfully in Excel
- **AND** all sheet names and headers SHALL match specification
- **AND** data SHALL be populated from database connections

#### Scenario: Overview Sheet Content
- **GIVEN** an Excel workbook generated for a specific MSA and asset
- **WHEN** the Overview sheet is examined
- **THEN** it SHALL contain executive summary with key metrics
- **AND** include market score, asset fit score, and risk assessment
- **AND** display pillar scores with visualizations
- **AND** show deal structure and archetype recommendations

#### Scenario: Market_Scorecard Sheet Functionality
- **GIVEN** the Market_Scorecard sheet in an exported workbook
- **WHEN** the sheet is analyzed
- **THEN** it SHALL contain complete market scoring data
- **AND** include all four pillar scores (Supply, Jobs, Urban, Outdoor)
- **AND** display normalized metrics (0-100) and final 0-5 scores
- **AND** show benchmark comparisons and trend data
- **AND** include interactive charts and conditional formatting

#### Scenario: Asset_Fit Sheet Evaluation
- **GIVEN** the Asset_Fit sheet in an exported workbook
- **WHEN** asset evaluation data is examined
- **THEN** it SHALL contain comprehensive asset fit analysis
- **AND** display product type compatibility scores
- **AND** show vintage and scope fit assessments
- **AND** include unit mix optimization recommendations
- **AND** provide parking and amenity fit scores

#### Scenario: Deal_Archetypes Sheet Analysis
- **GIVEN** the Deal_Archetypes sheet in an exported workbook
- **WHEN** deal structure data is examined
- **THEN** it SHALL contain complete deal archetype analysis
- **AND** display scope templates with cost and lift projections
- **AND** show ROI calculations and payback analysis
- **AND** include downtime scheduling and cadence optimization
- **AND** provide archetype ranking and recommendations

#### Scenario: Risk Sheet Assessment
- **GIVEN** the Risk sheet in an exported workbook
- **WHEN** risk data is examined
- **THEN** it SHALL contain comprehensive risk assessment
- **AND** display risk multipliers and severity indices
- **AND** show insurance requirements and deductible structures
- **AND** include climate and resilience risk factors
- **AND** provide mitigation strategies and contingency plans

#### Scenario: Ops_KPIs Sheet Performance
- **GIVEN** the Ops_KPIs sheet in an exported workbook
- **WHEN** operational data is examined
- **THEN** it SHALL contain operational performance metrics
- **AND** display reputation index and pricing guardrails
- **AND** show renovation cadence and downtime tracking
- **AND** include amenity ROI and program performance
- **AND** provide KPI trends and benchmarking

#### Scenario: CO-UT-ID_Patterns Sheet State Data
- **GIVEN** the CO-UT-ID_Patterns sheet in an exported workbook
- **WHEN** state-specific data is examined
- **THEN** it SHALL contain state-specific operational patterns
- **AND** display Colorado, Utah, and Idaho specific metrics
- **AND** show industry anchors and regulatory characteristics
- **AND** include peril profiles and winterization requirements
- **AND** provide state-specific tax cadence and guardrails

#### Scenario: Checklist Sheet Due Diligence
- **GIVEN** the Checklist sheet in an exported workbook
- **WHEN** due diligence items are examined
- **THEN** it SHALL contain complete diligence checklist
- **AND** display market, site, building, and financial/ops categories
- **AND** show status tracking and completion percentages
- **AND** include manual override logging with reason codes
- **AND** provide auto-population from data connectors

#### Scenario: Data_Lineage Sheet Provenance
- **GIVEN** the Data_Lineage sheet in an exported workbook
- **WHEN** data source information is examined
- **THEN** it SHALL contain complete data provenance tracking
- **AND** display source URLs, fetch timestamps, and data vintages
- **AND** show data quality metrics and validation results
- **AND** include metric definitions and calculation formulas
- **AND** provide audit trail for all data transformations

#### Scenario: Config Sheet Metadata
- **GIVEN** the Config sheet in an exported workbook
- **WHEN** configuration data is examined
- **THEN** it SHALL contain system configuration and run metadata
- **AND** display git SHA, config hash, and deterministic seeds
- **AND** show run context and lineage information
- **AND** include feature flags and environment settings
- **AND** provide data vintage and source information

#### Scenario: Functional Equivalence Validation
- **GIVEN** an Excel workbook generated from the same inputs as Python system
- **WHEN** values are compared between Python calculations and Excel formulas
- **THEN** the system SHALL achieve 95%+ value equivalence
- **AND** complex calculations SHALL replicate Python logic
- **AND** data connections SHALL provide live updates
- **AND** interactive elements SHALL function correctly

#### Scenario: Golden Master Testing
- **GIVEN** a reference Excel workbook with known correct values
- **WHEN** a new workbook is generated with same inputs
- **THEN** the system SHALL validate structural equivalence
- **AND** perform value-level comparison against golden master
- **AND** flag any deviations beyond acceptable tolerance
- **AND** maintain regression test suite for format consistency

