## Why
The project specification in project.md requires "PDF reports" as part of the export suite alongside Excel and Word formats, with "IC-ready scorecards and underwriting packets" that need to be print-ready and professional. However, the current system lacks PDF generation capabilities, forcing users to manually convert Word/Excel outputs or rely on external tools. A robust PDF engine is needed to create professional, print-ready reports with proper pagination, styling, and content that matches the Word memo format while providing fallbacks and comprehensive error handling.

## What Changes
- Implement PDF rendering engine with `exports.to_pdf(context, *, template_path, styles_path, outdir) -> Path` Python surface
- Create HTML-to-PDF rendering system using WeasyPrint (preferred) with ReportLab fallback
- Build comprehensive HTML template system with 10+ sections matching Word memo structure
- Implement robust pagination with CSS print rules and section anchoring
- Create mandatory appendix with data sources, methodology, and run metadata
- Add image handling with local asset resolution and broken image fallbacks
- Implement security controls preventing external HTTP loads during rendering
- Support both static generation and dynamic content with database connections
- Create comprehensive test suite with PDF content validation and determinism checks

**BREAKING**: None - this adds new PDF export functionality without modifying existing interfaces

## Impact
- Affected specs: `exports` (new PDF rendering requirements), `core` (enhanced export capabilities)
- Affected code: `src/aker_core/exports/`, HTML template system, CSS styling, image asset handling
- New dependencies: WeasyPrint (preferred), ReportLab (fallback), Jinja2 (templates), pdfminer.six (testing)
- Database impact: Enhanced export metadata tracking and asset reference resolution
- Testing: PDF content validation, rendering determinism, fallback functionality
