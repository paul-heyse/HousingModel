# Capability: Exports Suite

## Objective
Deliver investor-ready Excel exports that mirror Python-calculated analytics, preserving audit trails, definitions, and interactive insights for Investment Committee reviews.

## Key Outcomes
- `aker_core.exports.ExcelWorkbookBuilder` assembles the 10-sheet workbook with configuration, lineage, and KPI coverage aligned to the OpenSpec scenarios.
- `aker_core.exports.WordMemoBuilder` renders the IC-ready Word memo via docxtpl while enforcing inline image rules and footer metadata.
- `MemoContextBuilder` sanitises reviews (PII redaction) and prepares table/image payloads consumed by the Word builder.
- `MemoContextService` gathers market, asset, risk, ops, and state-pack data from repositories (with graceful fallbacks) before delegating to the builder.
- Workbooks embed run metadata (git SHA, config hash, feature flags) ensuring reproducibility and downstream compliance.
- Golden-master regression tests guard structural and numerical equivalence between Python and Excel outputs.

## Architecture Snapshot
- **Entry Points**: `aker_core.exports.to_excel`, `ExcelWorkbookBuilder.build_workbook`, `aker_core.exports.MemoContextService.build_context`, `aker_core.exports.to_word`.
- **Dependencies**: SQLAlchemy session for data fetches, `openpyxl` for workbook manipulation, `aker_core.markets` & `aker_core.asset` services for calculations.
- **Outputs**: XLSX files and DOCX memos written under `exports/`, optionally uploaded to S3/SharePoint by deployment scripts.
- **Integrations**: Pulls run metadata from `RunContext`, references definitions from knowledge base, links to governance checklist for closeout.

## Operational Workflow
1. Load deal context (MSA, asset id, as_of) with an active database session.
2. Instantiate `ExcelWorkbookBuilder(session)` and call `build_workbook`.
3. Workbook builders query domain tables (`market_scores`, `asset_fit`, `risk_metrics`, etc.) and render formatted tables/charts.
4. After persistence, share workbook with IC and archive path in governance artifact tracking.

## Data Lineage & Sources
| Source | Usage | Refresh Cadence | Notes |
|--------|-------|-----------------|-------|
| `market_scores`, `pillar_scores` | Market analytics | Nightly | Loaded via market scoring pipelines; referenced in Market_Scorecard sheet.
| `asset_fit`, `deal_archetypes` | Deal analytics | Per deal refresh | Fed by asset/ops engines; required for Asset_Fit & Deal_Archetypes sheets.
| `risk_metrics`, `state_packs` | Hazard & resilience | Weekly | Links to risk multipliers and state adjustments.
| `ops_metrics` | Operational KPIs | Weekly | Sourced from ops monitoring stack.
| `runs`, `lineage` | Metadata | Per export | Populates Config and Data_Lineage sheets.

## Validation & QA
- `tests/test_excel_exports.py` covers sheet generation, metadata stamping, and golden-master comparisons.
- `tests/test_word_memo.py` verifies memo rendering (no leftover template tokens, image presence, goldens, and review redactions).
- `tests/test_memo_service.py` exercises the memo context service fallbacks when repository data is unavailable.
- `tests/test_deal_ranking.py` + `tests/test_ops_engine.py` validate data dependencies consumed by export sheets.
- Manual QA follows the export runbook diff procedure before publishing to stakeholders.

## Runbooks
- [Exports Suite](../runbooks/exports-suite.md)

## Change Log
- 2024-06-04 — Knowledge base entry initiated with sheet coverage summary and validation hooks.
