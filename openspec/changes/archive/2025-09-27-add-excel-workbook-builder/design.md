## Context
The Aker property model requires comprehensive Excel export functionality that replicates the Python-based product's capabilities. Project.md specifies "Excel model configuration & results" with specific sheets and CLI command `aker report --msa=BOI --asset=Foo --as-of=2025-09-01 --format=pdf`. The current system lacks this export capability, requiring users to manually extract and format data.

## Goals / Non-Goals
- **Goals**:
  - Create functionally equivalent Excel workbook to Python system
  - Implement live data connections to PostgreSQL database
  - Build 10 specialized sheets with interactive elements
  - Support both static export and dynamic data connections
  - Achieve 95%+ functional equivalence with Python calculations
- **Non-Goals**:
  - Replace Python SDK functionality
  - Implement real-time collaboration in Excel
  - Create Excel-based data input forms (focus on output/reporting)

## Decisions

### Excel Workbook Architecture
- **Multi-Sheet Structure**: 10 specialized sheets with cross-references
- **Data Connections**: Live PostgreSQL connections for dynamic updates
- **Formula Replication**: Excel formulas that mirror Python calculations
- **Interactive Elements**: Pivot tables, charts, conditional formatting
- **Template System**: Reusable sheet templates with parameterized content

### Data Integration Strategy
- **Database Queries**: Optimized read queries for export data aggregation
- **Live Connections**: PostgreSQL data connections for real-time updates
- **Data Transformation**: Python-to-Excel formula mapping
- **Caching**: Export data caching for performance optimization

### Sheet-by-Sheet Implementation
Each sheet requires specific data extraction and formatting:

**Overview Sheet**:
- Executive summary dashboard
- Key performance indicators
- Visual charts and scorecards
- Cross-sheet navigation

**Market_Scorecard Sheet**:
- Pillar score calculations
- Benchmark comparisons
- Trend analysis
- Interactive score breakdowns

**Asset_Fit Sheet**:
- Asset evaluation matrices
- Fit score calculations
- Product type compatibility
- Guardrail compliance

**Deal_Archetypes Sheet**:
- Scope template library
- ROI calculations
- Payback analysis
- Archetype ranking

**Risk Sheet**:
- Risk matrix visualization
- Insurance requirement tables
- Mitigation strategy tracking
- Risk-adjusted return calculations

**Ops_KPIs Sheet**:
- Operational performance metrics
- Reputation index tracking
- Renovation cadence monitoring
- KPI trend analysis

**CO-UT-ID_Patterns Sheet**:
- State-specific operational data
- Industry anchor analysis
- Regulatory compliance tracking
- State-specific risk factors

**Checklist Sheet**:
- Due diligence status matrix
- Auto-population from data sources
- Manual override tracking
- Completion percentage calculations

**Data_Lineage Sheet**:
- Source provenance tracking
- Data vintage information
- Quality metrics
- Audit trail references

**Config Sheet**:
- Run metadata
- Configuration parameters
- Feature flag status
- Data source information

## Implementation Strategy

### Phase 1: Core Export Engine
```python
# Main export interface
class ExcelWorkbookBuilder:
    def __init__(self, session: Session):
        self.session = session
        self.workbook = None

    def build_workbook(self, msa: str, asset: str, as_of: date) -> Path:
        """Build complete Excel workbook with all sheets."""
        self.workbook = openpyxl.Workbook()

        # Build each sheet
        self._build_overview_sheet(msa, asset, as_of)
        self._build_market_scorecard_sheet(msa, asset, as_of)
        self._build_asset_fit_sheet(msa, asset, as_of)
        # ... additional sheets

        # Add data connections
        self._add_database_connections()

        # Save workbook
        output_path = self._generate_output_path(msa, asset, as_of)
        self.workbook.save(output_path)
        return output_path
```

### Phase 2: Sheet Template System
- **Template Classes**: Abstract base classes for sheet generation
- **Data Extraction**: Specialized queries for each sheet's data needs
- **Formula Generation**: Python-to-Excel formula translation
- **Styling**: Consistent formatting and conditional logic

### Phase 3: Data Connection Implementation
- **Query Optimization**: Efficient database queries for export data
- **Connection Strings**: Secure PostgreSQL connection configuration
- **Refresh Mechanisms**: Manual and automatic data refresh capabilities
- **Error Handling**: Graceful degradation when connections fail

### Phase 4: Interactive Features
- **Charts and Graphs**: Excel chart objects with dynamic data ranges
- **Pivot Tables**: Interactive data analysis capabilities
- **Conditional Formatting**: Visual indicators for key metrics
- **Named Ranges**: Cross-sheet data references

## Database Integration

### Export Data Queries
```sql
-- Market scorecard data
SELECT
    msa_id,
    supply_score_0_5,
    jobs_score_0_5,
    urban_score_0_5,
    outdoor_score_0_5,
    weighted_score_0_5,
    risk_multiplier
FROM pillar_scores
WHERE msa_id = $1 AND as_of = $2;

-- Asset fit data
SELECT
    asset_id,
    product_type,
    vintage_ok,
    unit_mix_fit,
    parking_fit,
    outdoor_enablers_ct,
    ev_ready_flag,
    fit_score
FROM asset_fit
WHERE asset_id = $1;
```

### Connection Configuration
```python
# PostgreSQL connection for Excel
connection_string = (
    f"Provider=SQLOLEDB;Data Source={db_host};"
    f"Initial Catalog={db_name};User ID={db_user};Password={db_password}"
)

# Excel data connection
connection = workbook.connections.add(
    name="AkerData",
    description="Live data from Aker property model",
    connection_string=connection_string
)
```

## Formula Replication Strategy

### Python-to-Excel Translation
```python
# Python calculation
def pillar_score(metrics: dict[str, float], weights: dict[str, float]) -> float:
    wsum = sum(weights.values())
    return sum(metrics[k]*weights[k] for k in weights) / wsum

# Excel equivalent
# =SUMPRODUCT(B2:B10, C2:C10) / SUM(C2:C10)
```

### Complex Calculation Mapping
- **Robust Min-Max**: `=MAX(0, MIN(100, (A1 - MIN(A:A)) / (MAX(A:A) - MIN(A:A)) * 100))`
- **Percentile Bucketing**: `=MATCH(A1, {0,20,40,60,80}, 1)`
- **Risk Multipliers**: `=A1 * B1 * C1` (compound risk factors)

## Performance Optimization

### Data Caching
- Export data cached for duration of workbook generation
- Query result caching with TTL for repeated exports
- Large dataset chunking for memory efficiency

### Batch Processing
- Parallel sheet generation where possible
- Batch database queries for multiple sheets
- Optimized data structures for Excel writing

### Memory Management
- Streaming data processing for large datasets
- Workbook generation in chunks
- Cleanup of temporary data structures

## Testing Strategy

### Golden Master Testing
```python
def test_excel_export_golden_master():
    """Test against reference Excel file."""
    # Generate workbook
    export_path = exports.to_excel("BOI", "SampleAsset", date.today())

    # Compare against golden master
    diff = compare_excel_files(export_path, "golden_master.xlsx")

    # Validate equivalence
    assert diff.max_difference < 0.01  # 1% tolerance
    assert diff.structure_matches
    assert diff.formula_equivalence
```

### Format Validation
- Sheet name validation
- Header structure verification
- Data type consistency
- Formula syntax validation

### Functional Equivalence
- Value comparison against Python calculations
- Interactive element functionality
- Data connection validation
- Cross-sheet reference integrity

## Migration Plan

1. **Phase 1**: Core export engine and Overview/Market_Scorecard sheets (Week 1-2)
2. **Phase 2**: Asset_Fit, Deal_Archetypes, Risk sheets (Week 3-4)
3. **Phase 3**: Ops_KPIs, CO-UT-ID_Patterns, Checklist sheets (Week 5-6)
4. **Phase 4**: Data_Lineage, Config sheets + data connections (Week 7-8)
5. **Phase 5**: Interactive features and performance optimization (Week 9-10)

### Rollback Strategy
- Feature flags control export functionality
- Database snapshots allow rollback to pre-export state
- Gradual rollout by sheet complexity

## Open Questions

- **Data Connection Security**: How to handle database credentials in Excel files?
- **Offline Functionality**: How to handle exports when database is unavailable?
- **Version Compatibility**: How to maintain compatibility with different Excel versions?
- **Large Dataset Handling**: How to optimize for exports with thousands of data points?
- **Interactive Element Limits**: What are the practical limits for Excel interactivity?
- **Formula Complexity**: How complex can Excel formulas get before becoming unmaintainable?

## Dependencies

### New Dependencies
- **openpyxl**: Excel file manipulation and formula generation
- **xlsxwriter**: High-performance Excel file creation
- **pandas**: Data manipulation and analysis for export data
- **sqlalchemy**: Database query optimization for export data

### Existing Dependencies
- **aker_core.database**: Database connection and query functionality
- **aker_core.markets**: Market scoring and pillar calculations
- **aker_core.asset**: Asset evaluation and fit scoring
- **aker_core.risk**: Risk assessment and mitigation
- **aker_core.ops**: Operational metrics and KPIs

This implementation will create a comprehensive Excel export system that maintains functional equivalence with the Python-based product while providing the interactive and visual capabilities that Excel users expect.
