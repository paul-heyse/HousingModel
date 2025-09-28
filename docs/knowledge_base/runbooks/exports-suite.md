# Runbook: Excel Export Generation

## Purpose
Generate, validate, and distribute Excel workbooks that mirror Python analytics for Investment Committee consumption.

## Preconditions
- `.venv` activated with `openpyxl`, `pandas`, and database drivers installed.
- Database populated with latest market, asset, risk metrics.
- `AKER_POSTGIS_DSN` points to read replica or primary with export permissions.
- Ensure `exports/` directory writable; optional `S3_BUCKET`/SharePoint credentials configured for uploads.

## Step-by-Step
1. **Warm scoring data** (optional but recommended)
   ```bash
   pytest tests/test_market_score_composer.py tests/test_asset_fit_engine.py
   ```
   Confirms upstream scoring logic passes before export.
2. **Generate workbook via Python shell**
   ```bash
   python - <<'PY'
   from datetime import date
   from sqlalchemy.orm import sessionmaker
   from aker_core.config import Settings
   from aker_core.exports import to_excel
   from aker_data.engine import create_engine_from_url

   settings = Settings()
   engine = create_engine_from_url(settings.postgis_dsn.get_secret_value())
   Session = sessionmaker(bind=engine)

   with Session() as session:
       path = to_excel(session=session, msa="DEN", asset="asset_123", as_of=date(2024, 6, 1))
       print(path)
   PY
   ```
   Record returned path and attach to governance artifacts tracker.
3. **Generate Word memo**
   ```bash
   python - <<'PY'
   from datetime import datetime
   from aker_core.exports import MemoContextService, to_word
   try:
       from aker_core.database import get_session
   except ImportError:
       get_session = None

   session = get_session() if get_session else None
   service = MemoContextService(session=session)
   payload = service.build_context(
       msa_id="DEN",
       run_id="run-demo",
       git_sha="abc1234",
       created_at=datetime.utcnow(),
       images={
           "pillar_bars": "exports/media/pillar_bars.png",
           "urban_isochrone": "exports/media/urban_isochrone.png",
           "roi_ladder": "exports/media/roi_ladder.png",
       },
   )

   context = dict(payload.data)
   context["_memo_meta"] = payload.metadata
   output = to_word(context)
   print(f"Memo written to {output}")

   if session is not None:
       session.close()
   PY
   ```
   - Ensure chart assets exist at 300 DPI (≤5.5" width). If a path is missing the rendered document will surface `[IMAGE MISSING: key]` and emit a warning.
   - The output directory defaults to `exports/word/`; pass `outdir="/path"` to override.

4. **Run golden-master regression (if applicable)**
   ```bash
   pytest tests/test_excel_exports.py -k golden
   ```
   Updates/new sheets require regenerating golden fixture via `pytest --update-golden` (document rationale in PR).
5. **Manual inspection**
   - Open workbook in Excel; verify sheet names, filters, slicers, and conditional formatting.
   - Confirm Config sheet includes `run_id`, git SHA, feature flags, and data vintages.
   - Check Data_Lineage sheet for missing datasets; rerun export if lineage incomplete.
   ```bash
   python - <<'PY'
   import pandas as pd
   wb = pd.ExcelFile('exports/aker_property_model_DEN_asset_123_20240601.xlsx')  # Replace with output path from step 2
   print(wb.parse('Market_Scorecard').head())
   PY
   ```
   Review printed metrics against pipeline logs; retain output in PR as verification evidence.
6. **Distribute**
   Upload workbook to designated storage (S3, SharePoint, Teams). Update governance checklist with link and attach run log.

## Validation
- `pytest tests/test_excel_exports.py` must pass.
- Compare key metrics (market score, asset fit, risk) against Python pipeline prints using the verification snippet in this runbook; attach results to the PR.
- Confirm workbook opens without compatibility warnings in Excel 365.

## Incident Response
- **Missing sheets**: Ensure `ExcelWorkbookBuilder` instantiates all builders; check logs for exceptions during `_build_*` calls.
- **Data mismatch**: Recompute upstream metrics; if still divergent, capture diff and create bug ticket referencing spec requirement.
- **File corruption**: Delete partial file in `exports/` and rerun. Validate disk space and antivirus scanning exclusions.

## References
- Capability brief: [capabilities/exports-suite.md](../capabilities/exports-suite.md)
- Spec: `openspec/specs/exports/spec.md`
- Governance checklist: see documentation gate template.
