## ADDED Requirements

### Requirement: ETL Inputs for Deal Ranking
The system SHALL provide ETL connectors and materializations to supply inputs required for ROI/payback computations and contextual adjustments for `deal_archetype` templates.

#### Scenario: Energy rates and tariffs
- **WHEN** refreshing monthly energy rates by site/region and tariff
- **THEN** the system makes rates available for cost/savings calculations

#### Scenario: Labor and material cost indices
- **WHEN** quarterly indices are refreshed by region
- **THEN** template costs are adjusted by index factors

#### Scenario: Asset baselines
- **WHEN** asset performance/utilization baselines are materialized
- **THEN** expected lift is computed against the correct baseline

#### Scenario: Downtime cost rates
- **WHEN** downtime cost tables by asset category are available
- **THEN** downtime costs are included in payback computation

#### Scenario: Vendor quotes override
- **WHEN** vendor quotes are ingested for specific scopes/assets
- **THEN** quotes MAY override template default costs with provenance captured


