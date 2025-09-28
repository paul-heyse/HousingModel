## 1. Specification & Design
- [ ] 1.1 Update exports spec with PDF rendering requirements covering HTML templates, CSS print rules, and appendix structure
- [ ] 1.2 Document API contract for `exports.to_pdf(context, *, template_path, styles_path, outdir)` function
- [ ] 1.3 Define HTML template structure with 10+ sections and anchor-based navigation
- [ ] 1.4 Design CSS print rules for pagination, styling, and responsive layout
- [ ] 1.5 Validate change with `openspec validate add-pdf-rendering-engine --strict`

## 2. Core PDF Engine Implementation
- [ ] 2.1 Implement `exports.to_pdf()` function with WeasyPrint primary and ReportLab fallback
- [ ] 2.2 Create HTML template rendering system with Jinja2 integration
- [ ] 2.3 Build CSS processing and print rule application system
- [ ] 2.4 Implement image asset resolution with local path handling
- [ ] 2.5 Add broken image fallback with bordered rectangle display

## 3. HTML Template System
- [ ] 3.1 Create HTML template with 10+ sections (cover, executive summary, market scorecard, etc.)
- [ ] 3.2 Implement section anchoring with id="sec-..." for TOC navigation
- [ ] 3.3 Build table rendering with zebra striping and sticky headers
- [ ] 3.4 Add image placeholder system with alt text fallbacks
- [ ] 3.5 Create responsive layout that adapts to PDF constraints

## 4. CSS Print Rules Implementation
- [ ] 4.1 Implement @page rules for A4 size and 18mm margins
- [ ] 4.2 Add page-break-before rules for section headers (h1)
- [ ] 4.3 Create page-break-inside: avoid rules for figures and tables
- [ ] 4.4 Implement font sizing rules (10pt for tables and legends)
- [ ] 4.5 Add zebra striping and sticky header CSS for table rendering

## 5. Appendix System
- [ ] 5.1 Create mandatory appendix with data sources & vintages table
- [ ] 5.2 Implement methodology section with normalization and weights description
- [ ] 5.3 Add run metadata section with run_id, git_sha, created_at, environment
- [ ] 5.4 Build table of contents with anchor-based navigation
- [ ] 5.5 Add appendix page numbering and section headers

## 6. Data Integration & Context Processing
- [ ] 6.1 Implement context key mapping from Python data to HTML template variables
- [ ] 6.2 Add database query integration for dynamic content generation
- [ ] 6.3 Create image asset path resolution system
- [ ] 6.4 Build data formatting and presentation layer
- [ ] 6.5 Add content sanitization for HTML-safe rendering

## 7. Error Handling & Fallbacks
- [ ] 7.1 Implement WeasyPrint availability detection and fallback to ReportLab
- [ ] 7.2 Create broken image path handling with bordered rectangle display
- [ ] 7.3 Add template rendering error handling with detailed diagnostics
- [ ] 7.4 Implement CSS parsing and validation with fallback defaults
- [ ] 7.5 Add file system error handling for asset loading

## 8. Security & Safety
- [ ] 8.1 Implement external HTTP load prevention during rendering
- [ ] 8.2 Add local asset path validation and sanitization
- [ ] 8.3 Create template injection prevention for dynamic content
- [ ] 8.4 Implement file size limits and processing timeouts
- [ ] 8.5 Add content sanitization for HTML and CSS injection prevention

## 9. Performance & Optimization
- [ ] 9.1 Implement PDF generation performance benchmarking
- [ ] 9.2 Add memory usage optimization for large document rendering
- [ ] 9.3 Create caching system for frequently used templates and assets
- [ ] 9.4 Implement parallel processing for multi-section document generation
- [ ] 9.5 Add compression and optimization for final PDF output

## 10. Testing & Quality Assurance
- [ ] 10.1 Create PDF content validation with pdfminer.six text extraction
- [ ] 10.2 Implement file size sanity checks (300KB-10MB range)
- [ ] 10.3 Add rendering determinism tests for identical input/output validation
- [ ] 10.4 Create golden master tests with reference PDF comparison
- [ ] 10.5 Add fallback functionality testing (WeasyPrint → ReportLab)
- [ ] 10.6 Implement accessibility testing for PDF content structure

## 11. Documentation & Deployment
- [ ] 11.1 Document PDF export API surface and configuration options
- [ ] 11.2 Create template customization guide for different report types
- [ ] 11.3 Add troubleshooting guide for common PDF generation issues
- [ ] 11.4 Create deployment configurations for production environment
- [ ] 11.5 Add monitoring and alerting for PDF generation health
