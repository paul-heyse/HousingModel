## Context
- Excel exports exist today, but no Word memo builder produces the IC-ready narrative requested in XPORT-002.
- The repo already has market, risk, asset, ops, and state-pack service stubs that can provide memo inputs; several return placeholder data that we must formalize for export usage.
- Word output must use docxtpl to populate an `ic_memo.docx` template that combines paragraphs, tables, charts, and metadata while preserving built-in Word styles.

## Goals / Non-Goals
- Goals: provide a deterministic `exports.to_word` surface, aggregate memo context from domain services, enforce styling/placeholder rules, and capture telemetry plus validation hooks.
- Non-Goals: build the GUI trigger UX beyond calling the export endpoint, produce PDF exports, or redesign upstream scoring/ops engines.

## Decisions
- Decision: Introduce a `WordMemoBuilder` (docxtpl wrapper) that accepts a validated context object and handles optional sections, images, and footer stamping.
- Decision: Create a `MemoContextBuilder` in `aker_core/exports` to materialize the `context` dict from domain repositories and sanitize reviews/ops copy.
- Decision: Store the base template at `templates/ic_memo.docx` and version it under source control; keep width-limited charts (<=5.5" wide, 300 DPI) under `/exports/media` at render time.
- Alternatives considered: reusing python-docx directly (more verbose, weaker templating); HTML-to-DOCX conversion (breaks Word styles, less control over placeholders).

## Risks / Trade-offs
- docxtpl introduces a new dependency; we mitigate by pinning a stable release and adding smoke tests that open the rendered DOCX via python-docx.
- Context data completeness depends on upstream services that remain partially stubbed; we will implement fallbacks and log structured warnings when inputs are missing.
- PII stripping for reviews could over-sanitize; provide targeted regex removals with unit coverage, and surface in telemetry if redactions occur.

## Migration Plan
1. Add dependency and template asset, ship builder/context modules behind unit tests.
2. Update GUI/CLI surfaces to call the new `exports.to_word` function once tests pass.
3. Document usage in runbooks and ensure telemetry dashboards ingest the new event type.

## Open Questions
- Should memo generation reuse existing chart-generation utilities or emit new static plots dedicated to Word exports?
- What repository should persist generated memos for audit (local disk vs. object storage)?
