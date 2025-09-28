## Why
Investment Committee packets currently rely on the Excel workbook export; there is no automated way to generate the IC narrative memo. Analysts have to stitch together charts, tables, and commentary manually, which is slow, inconsistent, and risks drifting from the quantitative outputs.

## What Changes
- Add a docxtpl-driven Word memo builder exposed via `exports.to_word(...)` that renders the IC narrative with consistent styling, tables, and inline images from the modeling context.
- Create a templated content pipeline that assembles memo inputs (market, asset, risk, operations, state packs, data vintages) and enforces the placeholder conventions described in XPORT-002.
- Handle edge cases for missing optional data or images, sanitize narrative content to strip PII from reviews, and emit structured telemetry `word_export_created` including image/table counts.
- Extend automated validation to cover memo generation (no leftover template tokens, media presence, heading checks, golden text comparison) and document how to run the export from CLI/GUI.

## Impact
- Affected specs: exports
- Affected code: `src/aker_core/exports`, `src/aker_gui/api/exports.py`, telemetry/logging utilities, doc generation helpers, test suite under `tests/`, `templates/`, `pyproject.toml`
