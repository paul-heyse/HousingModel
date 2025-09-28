## ADDED Requirements
### Requirement: Renovation Cadence Optimizer
The system SHALL provide an optimization engine for scheduling renovation work that maximizes renovation velocity while respecting vacancy caps and smoothing downtime across the portfolio.

#### Scenario: Basic Optimization With Vacancy Constraint
- **GIVEN** an asset with 100 units requiring 2 weeks downtime each and a 10% vacancy cap
- **WHEN** `ops.optimize_cadence(units=100, downtime_wk=2, vacancy_cap=0.1)` is called
- **THEN** the system SHALL return a weekly schedule that never exceeds 10% vacancy
- **AND** the total renovation time SHALL be minimized while respecting the constraint

#### Scenario: Downtime Smoothing Across Multiple Assets
- **GIVEN** a portfolio with multiple assets having different renovation requirements
- **WHEN** `ops.optimize_cadence()` is called with portfolio-level constraints
- **THEN** the system SHALL distribute renovation work to minimize peak vacancy periods
- **AND** downtime SHALL be smoothed across the schedule to avoid clustering

#### Scenario: Optimization Results Persistence
- **GIVEN** a completed optimization run
- **WHEN** the results are saved to the database
- **THEN** the `ops_model.cadence_plan` field SHALL contain the weekly schedule
- **AND** the plan SHALL include units renovated per week, expected vacancy rates, and total timeline

#### Scenario: Constraint Satisfaction Validation
- **GIVEN** an optimization plan
- **WHEN** validation tests are executed
- **THEN** the system SHALL verify that vacancy never exceeds the specified cap
- **AND** total downtime matches expected requirements
- **AND** the schedule is feasible given the input parameters
