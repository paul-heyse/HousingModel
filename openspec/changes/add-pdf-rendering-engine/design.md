## Context
The Aker property model requires comprehensive PDF export functionality that mirrors Word memo content and provides professional, print-ready reports. Project.md specifies "PDF reports" as part of the export suite, requiring "IC-ready scorecards and underwriting packets" with proper formatting and pagination. The current system lacks PDF generation, forcing manual conversion from Word/Excel outputs.

## Goals / Non-Goals
- **Goals**:
  - Create print-ready PDF reports mirroring Word memo content
  - Implement robust pagination with CSS print rules
  - Provide comprehensive appendix with data sources and methodology
  - Support both WeasyPrint (preferred) and ReportLab (fallback) renderers
  - Ensure security with no external HTTP loads during rendering
  - Maintain functional equivalence with existing export systems
- **Non-Goals**:
  - Replace existing Word/Excel export functionality
  - Implement real-time PDF generation for live updates
  - Create advanced PDF editing capabilities

## Decisions

### PDF Rendering Architecture
- **Dual Renderer System**: WeasyPrint primary with ReportLab fallback for environments without WeasyPrint
- **HTML/CSS Pipeline**: Jinja2 templates with CSS print rules for professional styling
- **Asset Resolution**: Local file path handling with broken image fallbacks
- **Template System**: Modular HTML templates for different report sections

### Security and Safety Model
- **Local Assets Only**: All images and resources loaded from local filesystem
- **No External HTTP**: Prevent external resource loading during PDF generation
- **Input Sanitization**: HTML escaping and content validation
- **Resource Limits**: File size limits and processing timeouts

### Template and Styling Strategy
- **HTML Structure**: Semantic markup with section anchors for navigation
- **CSS Print Rules**: @page, page-break, and print-optimized styling
- **Responsive Design**: Layout adaptation for PDF constraints
- **Asset Integration**: Image placeholders with local path resolution

## Implementation Strategy

### Phase 1: Core PDF Engine
```python
# Main PDF export interface
class PDFRenderer:
    def __init__(self, template_path: Path, styles_path: Path):
        self.template_path = template_path
        self.styles_path = styles_path
        self.renderer = self._detect_renderer()

    def render_to_pdf(self, context: dict, output_path: Path) -> dict:
        """Render context to PDF with metadata."""
        # Load and render HTML template
        html_content = self._render_template(context)

        # Apply CSS styles
        styled_html = self._apply_styles(html_content)

        # Generate PDF
        if self.renderer == "weasyprint":
            self._render_weasyprint(styled_html, output_path)
        else:
            self._render_reportlab(styled_html, output_path)

        return {
            "output_path": output_path,
            "renderer": self.renderer,
            "page_count": self._get_page_count(output_path),
            "file_size": output_path.stat().st_size
        }
```

### Phase 2: Template System
- **HTML Templates**: Jinja2 templates for each report section
- **CSS Styling**: Print-optimized styles with @page rules
- **Asset Integration**: Image placeholder system with local path resolution
- **Section Anchoring**: id="sec-..." anchors for TOC navigation

### Phase 3: Renderer Implementation
- **WeasyPrint Primary**: Full HTML/CSS support with advanced layout
- **ReportLab Fallback**: Text-first PDF generation for basic compatibility
- **Feature Detection**: Automatic renderer selection based on availability
- **Error Handling**: Graceful degradation with detailed diagnostics

### Phase 4: Security and Safety
- **Asset Validation**: Local path validation for all resource references
- **Content Sanitization**: HTML escaping and injection prevention
- **Resource Limits**: File size and processing timeout enforcement
- **Audit Logging**: Security event tracking without sensitive data

## PDF Template Structure

### HTML Template Sections
```html
<!DOCTYPE html>
<html>
<head>
    <title>Aker Property Model Report</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Cover Page -->
    <div id="sec-cover" class="cover-page">
        <h1>Aker Property Model</h1>
        <h2>{{ asset_name }} - {{ msa_name }}</h2>
        <p>Report Date: {{ report_date }}</p>
    </div>

    <!-- Executive Summary -->
    <div id="sec-executive-summary">
        <h1>Executive Summary</h1>
        <!-- Summary content -->
    </div>

    <!-- Market Scorecard -->
    <div id="sec-market-scorecard">
        <h1>Market Scorecard</h1>
        <!-- Pillar scores and analysis -->
    </div>

    <!-- Asset Fit -->
    <div id="sec-asset-fit">
        <h1>Asset Fit Analysis</h1>
        <!-- Asset evaluation data -->
    </div>

    <!-- Deal Archetypes -->
    <div id="sec-deal-archetypes">
        <h1>Deal Archetype Analysis</h1>
        <!-- Deal structure and ROI -->
    </div>

    <!-- Risk Assessment -->
    <div id="sec-risk-assessment">
        <h1>Risk Assessment</h1>
        <!-- Risk analysis and mitigation -->
    </div>

    <!-- State Patterns -->
    <div id="sec-state-patterns">
        <h1>State-Specific Patterns</h1>
        <!-- CO/UT/ID operational data -->
    </div>

    <!-- Appendix -->
    <div id="sec-appendix">
        <h1>Appendix</h1>
        <!-- A. Data Sources, B. Methodology, C. Run Metadata -->
    </div>
</body>
</html>
```

### CSS Print Rules
```css
@page {
    size: A4;
    margin: 18mm;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
    }
}

h1 {
    page-break-before: always;
    font-size: 18pt;
    font-weight: bold;
    margin-top: 0;
}

.figure, .table {
    page-break-inside: avoid;
}

.table {
    font-size: 10pt;
    border-collapse: collapse;
    width: 100%;
}

.table th {
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    padding: 8px;
    font-weight: bold;
}

.table td {
    border: 1px solid #ccc;
    padding: 8px;
}

.table tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* Sticky table headers */
.table thead {
    display: table-header-group;
}

/* Image handling */
img {
    max-width: 100%;
    height: auto;
    page-break-inside: avoid;
}

/* Broken image fallback */
img[src*="missing"] {
    border: 2px dashed #ff0000;
    background-color: #ffe0e0;
    padding: 20px;
    text-align: center;
    font-style: italic;
    color: #666;
}
```

## API Design

### Main Export Function
```python
def to_pdf(
    context: dict,
    *,
    template_path: Path | str = "templates/ic_report.html.j2",
    styles_path: Path | str = "templates/ic_report.css",
    outdir: Path | str | None = None
) -> Path:
    """Generate PDF report from context data.

    Args:
        context: Dictionary containing report data
        template_path: Path to Jinja2 HTML template
        styles_path: Path to CSS stylesheet
        outdir: Output directory (defaults to 'exports/')

    Returns:
        Path to generated PDF file

    Raises:
        FileNotFoundError: If template or styles files don't exist
        RenderingError: If PDF generation fails
        SecurityError: If external resources are referenced
    """
```

### Context Data Structure
```python
context = {
    # Report metadata
    "report_title": "Aker Property Model Report",
    "asset_name": "Sample Asset",
    "msa_name": "Boise",
    "report_date": "2024-09-15",

    # Executive summary
    "executive_summary": "...",

    # Market scorecard data
    "market_scores": {...},
    "pillar_breakdown": [...],

    # Asset fit data
    "asset_fit_scores": {...},
    "fit_recommendations": [...],

    # Deal archetypes
    "deal_archetypes": [...],
    "archetype_rankings": [...],

    # Risk assessment
    "risk_matrix": [...],
    "risk_mitigation": [...],

    # State patterns
    "state_patterns": {...},
    "regulatory_data": [...],

    # Appendix data
    "data_sources": [...],
    "methodology": "...",
    "run_metadata": {...}
}
```

## Renderer Implementation

### WeasyPrint Primary Renderer
```python
def _render_weasyprint(self, html_content: str, output_path: Path):
    """Render HTML to PDF using WeasyPrint."""
    from weasyprint import HTML, CSS

    # Load CSS
    with open(self.styles_path, 'r') as f:
        css_content = f.read()

    # Create HTML and CSS objects
    html_doc = HTML(string=html_content)
    css_doc = CSS(string=css_content)

    # Render to PDF
    html_doc.write_pdf(
        output_path,
        stylesheets=[css_doc],
        base_url=self.template_path.parent
    )
```

### ReportLab Fallback Renderer
```python
def _render_reportlab(self, html_content: str, output_path: Path):
    """Render text-first PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    # Create PDF document
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()

    # Extract text content from HTML (simplified)
    text_content = self._extract_text_from_html(html_content)

    # Build PDF content
    story = []

    for section in text_content:
        if section["type"] == "heading":
            story.append(Paragraph(section["text"], styles['Heading1']))
        elif section["type"] == "paragraph":
            story.append(Paragraph(section["text"], styles['Normal']))
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
```

## Security Implementation

### Asset Path Validation
```python
def _validate_asset_path(self, asset_path: str) -> bool:
    """Validate that asset path is local and safe."""
    if not asset_path:
        return False

    # Convert to Path and resolve
    path = Path(asset_path).resolve()

    # Check if path is within allowed directories
    allowed_dirs = [self.assets_base_path]
    for allowed_dir in allowed_dirs:
        try:
            path.relative_to(allowed_dir)
            return True
        except ValueError:
            continue

    return False

def _sanitize_html_content(self, html_content: str) -> str:
    """Sanitize HTML content to prevent injection."""
    import html

    # Escape HTML entities
    sanitized = html.escape(html_content)

    # Remove potentially dangerous tags/attributes
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)

    return sanitized
```

## Testing Strategy

### PDF Content Validation
```python
def test_pdf_content_extraction():
    """Test PDF content extraction and validation."""
    from pdfminer.high_level import extract_text

    # Generate PDF
    output_path = to_pdf(test_context)

    # Extract text content
    extracted_text = extract_text(str(output_path))

    # Validate required sections
    assert "Executive Summary" in extracted_text
    assert "Market Scorecard" in extracted_text
    assert "Appendix" in extracted_text

    # Validate data presence
    assert "4.2" in extracted_text  # Sample score
    assert "Sample Asset" in extracted_text  # Asset name
```

### Determinism Testing
```python
def test_pdf_determinism():
    """Test that identical inputs produce identical outputs."""
    # Generate two PDFs with same input
    output1 = to_pdf(test_context)
    output2 = to_pdf(test_context)

    # Compare file contents (excluding metadata timestamps)
    content1 = extract_pdf_content(output1)
    content2 = extract_pdf_content(output2)

    assert content1 == content2

    # Clean up
    output1.unlink()
    output2.unlink()
```

### Size Sanity Checks
```python
def test_pdf_size_sanity():
    """Test PDF file size is within acceptable range."""
    output_path = to_pdf(test_context)

    file_size = output_path.stat().st_size
    assert 100 * 1024 <= file_size <= 10 * 1024 * 1024  # 100KB - 10MB

    output_path.unlink()
```

## Migration Plan

1. **Phase 1**: Core PDF engine with WeasyPrint primary (Week 1-2)
2. **Phase 2**: ReportLab fallback implementation (Week 3-4)
3. **Phase 3**: Template system and CSS styling (Week 5-6)
4. **Phase 4**: Security, error handling, and testing (Week 7-8)
5. **Phase 5**: Integration with existing export system (Week 9-10)

### Rollback Strategy
- Feature flags control PDF export availability
- Database snapshots allow rollback to pre-PDF state
- Gradual rollout by report complexity and user role

## Dependencies

### New Dependencies
- **weasyprint**: Primary HTML-to-PDF renderer (preferred)
- **reportlab**: Fallback text-first PDF renderer
- **jinja2**: HTML template rendering
- **pdfminer.six**: PDF content extraction for testing
- **cssutils**: CSS parsing and validation

### Existing Dependencies
- **aker_core.exports**: Export system integration
- **aker_core.database**: Data access for report content
- **aker_core.markets**: Market scoring data
- **aker_core.asset**: Asset evaluation data
- **aker_core.ops**: Operational metrics and reputation data

This implementation will create a comprehensive PDF export system that provides professional, print-ready reports with the same content quality as Word memos while maintaining security and performance standards.
