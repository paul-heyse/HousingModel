## ADDED Requirements
### Requirement: Supply Constraint Calculators
The system MUST provide reusable calculators for supply elasticity, vacancy, and lease-up time on market to populate `market_supply` fields and support inverse scoring.

#### Scenario: Elasticity Calculator
- **WHEN** `supply.elasticity(permits, households)` is called with a three-year trailing average of permits issued and the corresponding households estimate
- **THEN** the helper SHALL return permits per 1,000 households with input validation for non-negative values
- **AND** the result SHALL populate the `market_supply.elasticity_idx` (or successor) field for downstream scoring

#### Scenario: Vacancy Calculator
- **WHEN** `supply.vacancy()` ingests HUD vacancy data for a market
- **THEN** the helper SHALL normalise the rate to a 0–1 fraction, flag out-of-range inputs, and write the value into the `market_supply.vacancy_rate` column
- **AND** the calculator SHALL expose inverse scoring guidance so higher vacancy lowers supply pressure scores

#### Scenario: Lease-Up Time On Market Calculator
- **WHEN** `supply.leaseup_tom()` is called with multifamily lease-up telemetry
- **THEN** the helper SHALL compute an average time-on-market in days, clamp implausible values, and persist the result into `market_supply.leaseup_tom_days`
- **AND** the helper SHALL emit an inverse score (lower days => higher score) for integration with pillar scoring

#### Scenario: Validation Coverage
- **WHEN** the calculators are executed in tests
- **THEN** unit tests SHALL cover nominal, boundary, and inverse-scoring cases, and Great Expectations suites SHALL enforce acceptable ranges for the affected `market_supply` columns
- **AND** validation SHALL fail fast on negative inputs or missing market identifiers, preventing persistence of invalid constraint metrics
