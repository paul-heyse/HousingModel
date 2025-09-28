## 1. Implementation
- [x] 1.1 Add `docxtpl` dependency and scaffold `templates/ic_memo.docx` with the required placeholders/styles.
- [x] 1.2 Introduce a memo context builder that assembles the `context` dict (market, asset, tables, risk, ops, state pack, images, data vintages, run metadata) and strips PII from reviews.
- [x] 1.3 Implement a `WordMemoBuilder` plus `exports.to_word(...)` convenience surface that renders the template, fills tables/images, applies optional-section fallbacks, and writes to the chosen output directory.
- [x] 1.4 Add structured telemetry/logging (`word_export_created`, missing-image warnings) and wire the FastAPI `/exports/word` endpoint to call the new export.
- [x] 1.5 Ensure image generation utilities save 300 DPI assets at <=5.5" width and register them in the memo context.

## 2. Testing & Validation
- [x] 2.1 Create unit/integration tests that render a memo with fixture data, unzip the DOCX to check media presence, scan for leftover `{{`/`{%` tokens, and confirm headings exist.
- [x] 2.2 Establish a golden-text comparison (timestamp-normalized) and verify telemetry payload contents in tests.

## 3. Documentation & Ops
- [x] 3.1 Update export runbook / knowledge base with Word memo instructions and validation steps.
- [x] 3.2 Document new CLI usage or sample script for generating the memo in README or docs.
