## Why
The project specification in project.md requires "Excel model configuration & results" with specific sheets (Overview, Market_Scorecard, Asset_Fit, Deal_Archetypes, Risk, Ops_KPIs, CO-UT-ID_Patterns, Checklist, Data_Lineage, Config) and CLI command `aker report --msa=BOI --asset=Foo --as-of=2025-09-01 --format=pdf`. However, the current system lacks a comprehensive Excel export system that replicates the Python-based product's functionality. Users need one-click Excel generation that maintains functional equivalence with the core system, including live data connections and calculated metrics.

## What Changes
- Implement Excel workbook builder with `exports.to_excel(msa, asset, as_of) -> Path` Python surface
- Create new `exports` capability with comprehensive workbook generation
- Build 10 specialized sheets with functional equivalence to Python system:
  - **Overview**: Executive summary with key metrics and visualizations
  - **Market_Scorecard**: Complete market scoring with pillar breakdowns
  - **Asset_Fit**: Asset evaluation and fit scoring
  - **Deal_Archetypes**: Deal structure and archetype analysis
  - **Risk**: Risk assessment and mitigation strategies
  - **Ops_KPIs**: Operational metrics and performance indicators
  - **CO-UT-ID_Patterns**: State-specific operational patterns
  - **Checklist**: Due diligence checklist with status tracking
  - **Data_Lineage**: Data source provenance and vintage tracking
  - **Config**: System configuration and run metadata
- Implement data connections to PostgreSQL database for live data
- Create Excel formulas that replicate Python calculations
- Add interactive elements (pivot tables, charts, conditional formatting)
- Support both static export and dynamic data connections

**BREAKING**: None - this adds new export functionality without modifying existing interfaces

## Impact
- Affected specs: New `exports` capability for Excel workbook generation
- Affected code: `src/aker_core/exports/`, database query optimizations for export data
- New dependencies: openpyxl, xlsxwriter, pandas (for data manipulation)
- Database impact: Optimized read queries for export data aggregation
- Testing: Golden master testing with sample data, format validation, functional equivalence verification
