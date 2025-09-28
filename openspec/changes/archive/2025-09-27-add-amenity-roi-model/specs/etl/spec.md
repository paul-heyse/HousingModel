## ADDED Requirements
### Requirement: Amenity Benchmark ETL Pipelines
The ETL platform SHALL ingest and refresh amenity benchmark datasets (capex, opex, utilization, membership uptake, vendor pricing) that power the amenity ROI engine, producing normalized tables keyed to amenity codes and asset contexts.

#### Scenario: Vendor Cost & Utilization Benchmarks
- **GIVEN** partner/vendor APIs or CSV extracts providing amenity installation costs, operating expenses, and utilization rates (e.g., cowork lounges, pet spas, smart access)
- **WHEN** `etl.amenities.load_vendor_benchmarks` runs on the scheduled cadence
- **THEN** the pipeline SHALL normalize values to standard units (cost per door, opex per unit per month, utilization %), attach data vintages, and persist outputs with lineage entries tied to the active run

#### Scenario: Membership Revenue Data
- **GIVEN** membership or subscription data feeds (cowork passes, fitness memberships, parking subscriptions)
- **WHEN** `etl.amenities.load_membership_revenue` executes
- **THEN** the ETL SHALL aggregate monthly revenue per amenity, map to assets/MSAs, and expose distributions for the ROI engine with documented refresh cadence (e.g., monthly)

#### Scenario: Resident Sentiment & Retention Metrics
- **WHEN** `etl.amenities.load_retention_signals` ingests data from CRM/renewal systems or surveys
- **THEN** the pipeline SHALL compute retention deltas attributable to specific amenities, store confidence intervals, and surface these metrics to the evaluation engine

#### Scenario: Data Quality & Monitoring
- **WHEN** amenity ETL flows run
- **THEN** Great Expectations suites SHALL validate schema/ranges (non-negative costs, utilization within 0–1), anomalies SHALL trigger metrics/alerts, and parquet extracts SHALL be versioned by amenity code and `as_of` partition

#### Scenario: Downstream Access
- **WHEN** the amenity ROI engine requests benchmark inputs
- **THEN** the ETL outputs SHALL be available through `aker_data.amenities` data access helpers, supporting both batch computation and interactive what-if analysis
