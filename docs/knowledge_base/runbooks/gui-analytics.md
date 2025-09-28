# Runbook: GUI Operations & Smoke Testing

## Purpose
Start the Dash-based analyst interface, validate core navigation and charts, and capture evidence for release readiness.

## Preconditions
- `.venv` activated with GUI dependencies (`dash`, `dash-bootstrap-components`, `dash-leaflet`).
- Backend services available: PostGIS, Prefect API (optional), exports directory.
- Environment variables set (`AKER_POSTGIS_DSN`, feature flags) and `.env` loaded.
- For remote analysts, ensure reverse proxy or SSH tunnel configured per deployment guide.

## Step-by-Step
1. **Launch FastAPI + Dash server**
   ```bash
   python -m aker_gui.app --host 0.0.0.0 --port 8050
   ```
   Wait for log message `Application startup complete`; open `http://localhost:8050/app/`.
2. **Run CLI health check**
   ```bash
   curl http://localhost:8050/api/health
   ```
   Response should be `{"status": "ok"}`; otherwise inspect server logs.
3. **Validate Market Scorecard page**
   - Navigate to `/app/markets`.
   - Confirm metrics cards render (Supply, Jobs, Urban, Outdoor). Values should match latest run context.
   - Interact with market selector; ensure map and charts update without client errors.
4. **Test Deal Workspace & Exports**
   - Load `/app/deal`, select active deal, confirm asset fit + risk tabs render.
   - Trigger Excel export from UI; verify toast notification and check `exports/` for new workbook (tie to exports runbook).
5. **Ops & Brand dashboard smoke**
   - Navigate to `/app/ops`; verify reputation index chart loads.
   - Cross-check values with `pytest tests/test_ops_brand_dashboard.py` output.
6. **Run automated smoke test (optional)**
   ```bash
   pytest tests/test_ops_brand_dashboard.py -k smoke
   ```
   Use `--maxfail=1` for quick signal; integrate with CI job as part of release checklist.

## Validation
- Screenshot each primary page and archive in release ticket.
- `pytest tests/test_ops_brand_dashboard.py` passes locally.
- No console errors in browser dev tools after navigation.

## Incident Response
- **Blank page**: Check server logs for callback exceptions; run with `--debug` to expose stack traces.
- **Data stale**: Run ETL pipelines per `runbooks/etl-pipelines.md` and refresh page; confirm `last refreshed` timestamp updates.
- **Export failure**: Inspect API response in browser network tab; cross-reference exports runbook for error resolution.

## References
- Capability brief: [capabilities/gui-analytics.md](../capabilities/gui-analytics.md)
- Spec: `openspec/specs/gui/spec.md`
- OpenSpec change in progress: `openspec/changes/add-ops-brand-dashboard`

