## 1. Specification
- [x] 1.1 Draft ETL integration requirements covering each data source family in `sources.yml` (demographics/labor/macro, supply/permits, housing market, hazard/risk, amenities/ops sentiment).
- [x] 1.2 Document lineage, validation, caching, and consumer-module mappings for each feed.
- [x] 1.3 Validate change with `openspec validate add-source-integration-roadmap --strict`.

## 2. Implementation Planning (post-approval)
- [x] 2.1 Inventory missing connectors or adapters per source and align with module owners.
- [x] 2.2 Sequence ETL build-out (priority feeds, cadence, dependencies) and tie into Prefect flows.
- [x] 2.3 Define acceptance criteria for stubbing vs. production connectors during phased rollout.

## 3. Follow-up
- [x] 3.1 Update engineering roadmap / link to relevant change requests once implementation milestones are scheduled.
