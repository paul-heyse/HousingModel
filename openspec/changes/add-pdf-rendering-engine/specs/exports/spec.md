## ADDED Requirements
### Requirement: PDF Rendering Engine
The system SHALL provide a comprehensive PDF rendering engine that generates print-ready reports mirroring Word memo content with robust pagination, comprehensive appendix, and professional styling.

#### Scenario: PDF Generation with WeasyPrint
- **GIVEN** a valid context dictionary with report data
- **WHEN** `exports.to_pdf(context, template_path="templates/ic_report.html.j2", styles_path="templates/ic_report.css")` is called
- **THEN** the system SHALL use WeasyPrint to render HTML to PDF
- **AND** apply CSS print rules for proper pagination and styling
- **AND** generate a PDF with all required sections and professional formatting
- **AND** return the path to the generated PDF file

#### Scenario: ReportLab Fallback Rendering
- **GIVEN** WeasyPrint is unavailable in the environment
- **WHEN** `exports.to_pdf()` is called
- **THEN** the system SHALL automatically fallback to ReportLab text-first PDF generation
- **AND** log a warning indicating "renderer=reportlab" in metadata
- **AND** generate a functional PDF with basic content structure
- **AND** maintain the same API contract and return format

#### Scenario: HTML Template Structure and Anchoring
- **GIVEN** an HTML template for IC reports
- **WHEN** the template is processed
- **THEN** it SHALL contain sections for cover, executive summary, market scorecard, urban/outdoor figures, asset fit, deal archetypes, risk, state pack, and appendix
- **AND** each section SHALL have id="sec-..." for TOC navigation
- **AND** support manual table of contents with {title, anchor_id} structure
- **AND** include image placeholders with {{ url_for_asset('filename') }} helper

#### Scenario: CSS Print Rules and Pagination
- **GIVEN** CSS print styles for PDF generation
- **WHEN** PDF is rendered
- **THEN** @page rules SHALL set A4 size with 18mm margins
- **AND** h1 elements SHALL have page-break-before: always
- **AND** .figure and .table elements SHALL have page-break-inside: avoid
- **AND** font sizes SHALL be optimized for print (10pt for tables and legends)
- **AND** tables SHALL have zebra striping and sticky headers

#### Scenario: Mandatory Appendix Content
- **GIVEN** a generated PDF report
- **WHEN** the appendix section is examined
- **THEN** it SHALL contain "A. Data sources & vintages" table with source, vintage, and link information
- **AND** include "B. Methodology" section with normalization and weights description
- **AND** contain "C. Run metadata" with run_id, git_sha, created_at, and environment information
- **AND** support table of contents with anchor-based navigation

#### Scenario: Image Asset Resolution and Fallbacks
- **GIVEN** HTML template with image references
- **WHEN** PDF is generated
- **THEN** the system SHALL resolve {{ url_for_asset('filename') }} to local file paths
- **AND** broken image paths SHALL produce bordered rectangles with alt text
- **AND** all image assets SHALL be loaded from local filesystem only
- **AND** no external HTTP loads SHALL occur during rendering

#### Scenario: PDF Content Validation and Testing
- **GIVEN** a generated PDF file
- **WHEN** validation tests are executed
- **THEN** the system SHALL extract text content using pdfminer.six
- **AND** verify presence of required section titles and content
- **AND** check file size is within acceptable range (300KB-10MB)
- **AND** validate deterministic rendering (identical inputs produce identical outputs)
- **AND** confirm all sections and subsections are properly formatted

#### Scenario: Security and Safety Constraints
- **GIVEN** PDF generation process
- **WHEN** rendering HTML and CSS
- **THEN** no external HTTP loads SHALL be permitted during rendering
- **AND** all assets SHALL be validated as local file paths
- **AND** template injection SHALL be prevented through proper escaping
- **AND** file size limits SHALL be enforced to prevent resource exhaustion
- **AND** processing timeouts SHALL prevent infinite rendering loops

#### Scenario: Error Handling and Recovery
- **GIVEN** PDF generation with missing or invalid inputs
- **WHEN** rendering fails
- **THEN** the system SHALL provide detailed error diagnostics
- **AND** broken image paths SHALL render as bordered rectangles with alt text
- **AND** CSS parsing errors SHALL fallback to default styling
- **AND** template rendering errors SHALL provide context about failure location
- **AND** maintain graceful degradation for partial failures

#### Scenario: Performance and Resource Management
- **GIVEN** large datasets or complex templates
- **WHEN** PDF generation is executed
- **THEN** the system SHALL process data in chunks to manage memory
- **AND** implement caching for frequently used templates and assets
- **AND** support parallel processing for multi-section document generation
- **AND** add compression and optimization for final PDF output
- **AND** monitor memory usage and prevent resource exhaustion

#### Scenario: Integration with Existing Export System
- **GIVEN** the existing Excel and Word export capabilities
- **WHEN** PDF export is added
- **THEN** the system SHALL use the same context data structure
- **AND** maintain consistent data formatting and presentation
- **AND** support the same CLI interface patterns
- **AND** integrate with existing export metadata and audit trails
- **AND** provide unified export API surface
