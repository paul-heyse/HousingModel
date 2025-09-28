## 1. Specification & Design
- [x] 1.1 Finalize guardrail categories and default thresholds per context
- [x] 1.2 Define `AssetFitResult` structure and flag taxonomy
- [x] 1.3 Confirm persistence schema `asset_fit` and lineage fields

## 2. ETL Connectors
- [x] 2.1 Implement asset attributes connector (product type, vintage, unit mix/size, ceiling, W/D)
- [x] 2.2 Implement parking and transit context enrichment connector
- [x] 2.3 Implement regulatory rules connector (parking, W/D, accessibility) with geo scope
- [x] 2.4 Implement market comps connector for reference distributions
- [x] 2.5 Add validation (Great Expectations) suites for ETL artifacts

## 3. Engine Implementation
- [x] 3.1 Implement `asset.fit(asset_id|spec, context)` API
- [x] 3.2 Implement guardrail checks and weighting for 0–100 score
- [x] 3.3 Implement deterministic evaluation with versioned rulesets
- [x] 3.4 Implement persistence to `asset_fit` with inputs and overrides

## 4. CLI & Batch
- [x] 4.1 Add CLI to run fit on single asset and batches
- [x] 4.2 Add export of scenario table with flags and arithmetic breakdown

## 5. Tests & DoD
- [x] 5.1 Wizard examples produce expected flags
- [x] 5.2 Unit tests for each guardrail category
- [x] 5.3 End‑to‑end test from ETL → fit → export

## 6. Documentation
- [x] 6.1 README and examples for developers
- [x] 6.2 Policy configuration guide and overrides


