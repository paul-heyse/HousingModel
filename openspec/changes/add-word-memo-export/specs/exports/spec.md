## ADDED Requirements
### Requirement: Word Investment Memo Export
The exports package SHALL generate an IC-ready Word investment memo using a docxtpl template fed by a validated context dictionary and produce deterministic output files on disk.

#### Scenario: to_word Renders Memo With Template Placeholders
- **GIVEN** a context dict containing `msa`, `market_tables`, `risk`, `data_vintage`, `run_id`, `git_sha`, `created_at`, and `images`, with optional `asset`, `ops`, `state_pack`
- **WHEN** `exports.to_word(context, template_path="templates/ic_memo.docx", outdir=exports_dir)` is called
- **THEN** the docxtpl renderer SHALL populate the cover with `{{ msa.name }}`, `{{ msa.as_of }}`, `{{ run_id }}`, and `{{ git_sha }}`
- **AND** the executive summary paragraph SHALL interpolate `{{ msa.pillar_scores.weighted_0_5 }}` and `{{ msa.pillar_scores.risk_multiplier }}`
- **AND** inline images SHALL use the provided paths with `InlineImage(doc, images.pillar_bars, width=Inches(5.5))`, `images.urban_isochrone`, and `images.roi_ladder`, each backed by a 300 DPI asset capped at 5.5 inches wide
- **AND** market tables SHALL loop through `market_tables.supply`, `jobs`, `urban`, `outdoors` rendering the specified columns in Table Grid style
- **AND** when `asset` data exists it SHALL display `asset.fit_score` and render a flags table iterating `asset.flags`
- **AND** when `ops` data exists it SHALL present `ops.reputation_idx` and summarize `ops.nps_series` / `ops.reviews_series` in the memo narrative
- **AND** when `state_pack.changes` exist they SHALL render as a two-column "before → after" table using Table Grid style
- **AND** risk multipliers SHALL render rows from `risk.multipliers`, and data vintages SHALL iterate over each `data_vintage` entry
- **AND** the footer SHALL display `Created {{ created_at }} · Run {{ run_id }}` with page numbering, using Word built-in styles (Title, Heading 1/2/3, Normal, Table Grid)
- **AND** the function SHALL return the absolute `Path` to the generated `.docx`
- **AND** if `outdir` is omitted it SHALL write to the default `exports/word` directory, creating it if necessary

#### Scenario: Optional Sections Provide Standard Placeholder Messaging
- **GIVEN** a context missing `asset` or `ops` collections
- **WHEN** `exports.to_word` renders the memo
- **THEN** each absent section SHALL still include its heading styled per template
- **AND** the body SHALL contain a single sentence (`"No asset context provided"` or `"No operations data available"`) in Normal style

#### Scenario: Missing Images Yield Inline Placeholders and Warnings
- **GIVEN** the context references an image key that points to a non-existent file path
- **WHEN** `exports.to_word` renders the memo
- **THEN** the memo SHALL insert `[IMAGE MISSING: <key>]` text at the image location
- **AND** a warning SHALL be logged identifying the missing key and template block

#### Scenario: Telemetry and PII Safeguards
- **GIVEN** reviews content in `ops.reviews_series`
- **WHEN** `exports.to_word` processes the context
- **THEN** it SHALL strip raw PII artifacts (email addresses, phone numbers, customer names) before insertion
- **AND** emit a structured telemetry event `word_export_created` with counts of tables rendered, images embedded, redactions performed, and the resolved output path

#### Scenario: Memo Validation Tests Enforce Output Integrity
- **GIVEN** the automated test suite
- **WHEN** memo generation tests run
- **THEN** they SHALL unzip the DOCX and assert no remaining `{{` or `{%` tokens exist in document XML
- **AND** confirm required media assets under `/word/media` match the context
- **AND** search the document XML for key headings ("Executive Summary", "Appendix A – Data sources")
- **AND** compare normalized paragraphs against a golden baseline fixture (timestamp stripped)
