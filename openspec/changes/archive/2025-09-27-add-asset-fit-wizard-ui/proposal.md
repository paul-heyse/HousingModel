## Why
Analysts currently have only the placeholder Asset Fit page shipped with the initial Dash GUI change. It lacks the guided workflow, live fit scoring, guardrail surfacing, and mandate integration described in UI-004. Without these capabilities the GUI cannot replace the Python SDK/Excel workflow for fit analysis, forcing duplication of effort and preventing timely guardrail compliance reviews.

## What Changes
- Implement the Asset Fit Wizard route at `/app/asset-fit` with stepper navigation, dual-panel layout, and auto-save state management aligned with UI-004.
- Flesh out REST endpoints under `/api/assets/{asset_id}` and `/api/assets/fit`, plus guardrail mandate retrieval, including debounced calculation calls and role-aware persistence hooks.
- Add localStorage state caching, unsaved-changes indicators, flag interaction behavior, and blocking error banners for missing guardrails.
- Capture telemetry about flag frequency and enforce permission gates so only Analysts/Admins can persist fit reports.
- Extend GUI spec with explicit scenarios for inputs, flags, error handling, and tests/DoD.

## Impact
- Affected specs: `gui` (Asset Fit Wizard requirement updated with UX/contract details).
- Affected code: `src/aker_gui/dash_pages/asset_fit_wizard.py`, `src/aker_gui/api/assets.py`, shared state utilities, telemetry hooks.
- Dependencies: Dash components (dcc, dbc), browser storage helpers, existing asset fit calculation service.
- Risks: Medium – introduces new async interactions and client-side storage; mitigated by staged rollout and regression tests.
