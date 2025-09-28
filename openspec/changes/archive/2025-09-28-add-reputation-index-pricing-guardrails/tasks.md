## 1. Specification & Design
- [x] 1.1 Define index formula and weights (reviews vs NPS)
- [x] 1.2 Specify `ops_model` persistence fields and lineage

## 2. ETL Connectors
- [x] 2.1 Implement reviews connector (Google, Yelp, App/Play)
- [x] 2.2 Implement NPS connector (Delighted/Qualtrics/Medallia)
- [x] 2.3 Optional benchmark enrichment connector
- [x] 2.4 Add validation (Great Expectations) suites

## 3. Engine Implementation
- [x] 3.1 Implement `ops.reputation_index(reviews, nps)`
- [x] 3.2 Implement `ops.pricing_rules(index)`
- [x] 3.3 Persistence to `ops_model` with inputs/version

## 4. CLI & Batch
- [x] 4.1 CLI to run index calc and export guardrails

## 5. Tests & DoD
- [x] 5.1 Synthetic data shifts produce predictable index deltas
- [x] 5.2 Unit tests for bounds and monotonicity
- [x] 5.3 End‑to‑end ETL → index → rules test


