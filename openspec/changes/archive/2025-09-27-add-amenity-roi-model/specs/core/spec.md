## ADDED Requirements
### Requirement: Amenity ROI Evaluation Engine
The system SHALL provide an amenity ROI engine that evaluates a set of proposed amenities for an asset and returns quantified impacts across rent premium, retention improvement, ancillary membership revenue, and net operating income.

#### Scenario: Evaluate Amenity Package
- **GIVEN** an asset identifier and a list of amenities (e.g., `[{"code": "cowork_lounge", "capex": 2500, "opex": 180}]`)
- **WHEN** `amenity.evaluate(asset_id, amenities=amenities)` is invoked
- **THEN** the engine SHALL return an impact payload including projected `rent_premium_per_unit`, `retention_delta_bps`, `membership_revenue_per_month`, `payback_months`, and `noi_delta`
- **AND** results SHALL include the assumptions (benchmark source, utilization, pricing) used to calculate each impact

#### Scenario: Positive Premium And Retention Increase NOI
- **GIVEN** an amenity scenario with positive rent premium and retention delta per the project specification
- **WHEN** `amenity.evaluate` runs with base asset assumptions
- **THEN** the computed `noi_delta` SHALL increase relative to the baseline NOI and the test suite SHALL assert the increase against a fixture dataset

#### Scenario: Persist Amenity Program Records
- **WHEN** amenity evaluation completes
- **THEN** the system SHALL persist or update an `amenity_program` record with fields including `asset_id`, `amenity_code`, `capex`, `opex`, `rent_premium`, `retention_delta_bps`, `membership_revenue`, `payback_months`, `noi_delta`, `data_vintage`, `run_id`, and `calculation_method`
- **AND** duplicate amenity rows for the same asset SHALL be versioned via `effective_start/end` or overwritten within the active run, as defined in the design

#### Scenario: Reporting & Export Integration
- **WHEN** an investment memo, asset operations dashboard, or Excel export is generated for an asset with amenity evaluations stored
- **THEN** the report SHALL render an amenity ROI table summarising capex, opex, premiums, retention delta, membership revenue, payback, and NOI impact with data vintage and benchmark source annotations

#### Scenario: Tests & Definition Of Done
- **WHEN** automated tests execute for the amenity module
- **THEN** unit tests SHALL cover ROI math (premium/retention to NOI), scenario-based property tests SHALL validate monotonicity (higher utilization → higher ROI), and integration tests SHALL round-trip evaluation → persistence → report serialization
- **AND** golden fixtures SHALL protect against regression in the payback/NOI formulas for representative assets
