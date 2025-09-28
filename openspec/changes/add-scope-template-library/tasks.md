## 1. Implementation
- [ ] 1.1 Author spec deltas for `deal` capability (scope library, ROI ladder)
- [ ] 1.2 Author spec deltas for `etl` capability (rates, indices, baselines)
- [ ] 1.3 Validate specs: `openspec validate add-scope-template-library --strict`
- [ ] 1.4 Python API skeleton for `deal.rank_scopes(asset_id, scopes=[...])`
- [ ] 1.5 Define `deal_archetype` schema and pydantic/dataclass types
- [ ] 1.6 Implement ROI, payback, downtime cost calculations and thresholds
- [ ] 1.7 Deterministic tie‑break (ROI desc, downtime asc, cost asc)
- [ ] 1.8 Integrate materialized baselines (savings baseline, utilization)
- [ ] 1.9 Wire ETL inputs: energy rates, labor/material indices, downtime cost rates
- [ ] 1.10 Optional vendor quotes override

## 2. ETL & Data Quality
- [ ] 2.1 Add/extend connectors:
      energy_rates, cost_indices (labor/material), downtime_costs, asset_baselines, vendor_quotes
- [ ] 2.2 Great Expectations suites for ranges, required columns, and currency/units
- [ ] 2.3 Prefect flows for refresh cadence (monthly rates, quarterly indices)
- [ ] 2.4 Data lineage and freshness metrics

## 3. Tests
- [ ] 3.1 Unit tests for ROI/payback math and tie‑break
- [ ] 3.2 Scenario tests: ranked ordering matches expectation given templates
- [ ] 3.3 Payback guard enforces exclusion when exceeding threshold
- [ ] 3.4 Integration test with ETL inputs present

## 4. Definition of Done
- [ ] DoD.1 `openspec validate --strict` passes
- [ ] DoD.2 `ruff`, `black`, `pytest -q` pass
- [ ] DoD.3 Spec scenarios cover ranking and payback guard
- [ ] DoD.4 ETL connectors documented and scheduled; data quality checks in place

