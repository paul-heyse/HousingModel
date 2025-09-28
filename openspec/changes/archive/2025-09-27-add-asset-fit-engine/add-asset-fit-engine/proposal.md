## Why
Asset underwriting and product selection need a deterministic, explainable fit assessment against policy guardrails. Today, checks are manual and inconsistent across product types and markets.

## What Changes
- Implement `asset.fit(asset_id|spec, context) -> AssetFitResult(flags=[...], fit_score=0..100)`
- Encode guardrails for: product types, vintage bands, unit mix & size, ceiling heights, in‑unit W/D, and parking ratios by market context
- Add scenario and flag engine with human‑readable reasons and machine‑parseable codes
- Persist results to `asset_fit` schema with lineage (inputs, version, timestamp)
- Provide wizard examples and fixtures ensuring expected flags fire
- ETL connectors for asset attributes, regulatory minimums, parking/transit context, and comps

## Impact
- Affected specs: `asset` capability (fit engine and guardrails), `etl` capability (asset attributes & context connectors)
- Affected code: `aker_core.asset.fit`, repository for `asset_fit`, validation suites, CLI for batch evaluation

## Non‑Goals
- Full financial modeling (handled elsewhere); this focuses on policy fit not returns
- Design of UI—out of scope; we expose CLI and programmatic surface

## Open Questions
- Default weightings for partial compliance vs. strict gating
- Market overrides source of truth (DB vs. config repo)


