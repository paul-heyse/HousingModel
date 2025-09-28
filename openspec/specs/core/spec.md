# Core Configuration

## Purpose
Provide a 12-factor compliant configuration system with feature flags so runtime behaviour stays auditable, reproducible, and free of hard-coded secrets.
## Requirements
### Requirement: Environment-First Application Settings
The system SHALL expose a typed `aker_core.config.Settings` object backed by pydantic-settings that loads defaults, an optional project `.env`, and environment variables in 12-factor precedence (environment > `.env` > defaults) while excluding secrets from source control.

#### Scenario: Environment Overrides Dotenv And Defaults
- **GIVEN** a default value and an entry in `.env`
- **WHEN** an environment variable with the same key is set before loading settings
- **THEN** `Settings()` SHALL resolve the environment value and report its source as `env`

#### Scenario: Dotenv Overrides Defaults When Environment Missing
- **GIVEN** a default value defined in code and a `.env` entry
- **WHEN** the matching environment variable is absent
- **THEN** `Settings()` SHALL return the `.env` value and report its source as `dotenv`

#### Scenario: Resolved Configuration Can Be Snapshotted Without Secrets
- **WHEN** the settings object is serialised for testing or diagnostics
- **THEN** only non-secret fields SHALL appear in the snapshot and the structure SHALL remain stable for regression tests

### Requirement: Runtime Feature Flags
The feature flag system SHALL continue to resolve defaults, dotenv, and environment values in precedence order without behavioural changes from this refactor.

#### Scenario: Flag Resolution Remains Unchanged
- **WHEN** a feature flag is overridden via environment variables
- **THEN** `is_enabled()` SHALL reflect the environment value after logging optimizations

### Requirement: Cache Behaviour
The cache subsystem SHALL respect environment overrides (`AKER_CACHE_PATH`) and infer storage metadata (e.g., JSON vs Parquet) while exposing helper utilities for reading metadata.

#### Scenario: Cache Respects Environment Override
- **WHEN** `AKER_CACHE_PATH` is set and `Cache()` is constructed without a base path
- **THEN** artifacts SHALL be persisted beneath the override directory and metadata helper SHALL reflect the resolved path

#### Scenario: JSON Data Stores Metadata
- **WHEN** JSON-like data is stored without specifying `data_type`
- **THEN** the payload SHALL be saved under the inferred type with an adjacent metadata file indicating `data_type="json"`

### Requirement: Typed External Dependency Settings
Every external dependency (APIs, storage, services) SHALL have a corresponding typed field within `aker_core.config.Settings`, documenting required parameters and ensuring zero secrets are hard-coded.

#### Scenario: Missing Required Dependency Field Raises Validation Error
- **GIVEN** a required API key field without default
- **WHEN** settings are loaded without providing the value via environment or `.env`
- **THEN** pydantic SHALL raise a validation error indicating the missing field

#### Scenario: Optional Dependencies Default Safely
- **WHEN** an optional integration is not configured
- **THEN** `Settings()` SHALL provide a safe default (e.g., `None` or feature flag disabled) and refrain from enabling the integration implicitly

### Requirement: Immutable Run Context
The system SHALL provide a context manager `aker_core.run.RunContext` that records git SHA, configuration hash, deterministic seed values, start/end timestamps, and assigns a unique `run_id` that is propagated to all outputs and persisted in the `runs` table.

#### Scenario: Run Context Captures Execution Metadata
- **WHEN** a pipeline executes within `with RunContext() as run`
- **THEN** the resulting `run` SHALL expose `run.id`, `run.git_sha`, `run.config_hash`, `run.seed`, `run.started_at`, and `run.finished_at` populated from the environment and configuration

#### Scenario: Outputs Carry Run Identifier
- **WHEN** a pipeline writes model outputs while the context is active
- **THEN** each output record SHALL include the assigned `run_id`

### Requirement: Deterministic Reruns
The system SHALL guarantee deterministic reruns when inputs and configuration are unchanged by reusing stored seeds and configuration hashes to validate outputs against previously recorded runs.

#### Scenario: Identical Inputs Produce Matching Hash
- **GIVEN** a prior run with recorded configuration hash and seeds
- **WHEN** the pipeline is rerun with the same inputs and configuration
- **THEN** the new run SHALL produce an identical output hash and be marked as such in the run log

### Requirement: Lineage Logging
The system SHALL expose `run.log_lineage(table, source, url, fetched_at, hash)` to persist dataset lineage rows in the `lineage` table for every external dataset consumed during the run.

#### Scenario: Lineage Entry Recorded For Data Source
- **WHEN** `run.log_lineage("markets", "census", "https://census.gov", fetched_at, hash)` is called
- **THEN** the `lineage` table SHALL receive a row tying the resource metadata to the active `run_id`

#### Scenario: Lineage Requires Active Run Context
- **WHEN** `log_lineage` is called outside an active run context
- **THEN** the system SHALL raise an error indicating that lineage logging requires an active `RunContext`

### Requirement: Run Context Engine Management
The `with_run_context` decorator SHALL reuse database engines and session factories instead of recreating them for each invocation.

#### Scenario: Session Factory Reuse
- **WHEN** multiple tasks enter the run context within a flow
- **THEN** the underlying SQLAlchemy engine SHALL be reused (confirmed via test instrumentation) and run status SHALL persist even on meta-session commit errors

### Requirement: Hexagonal Port Definitions
The system SHALL define abstract port interfaces for MarketScorer, AssetEvaluator, DealArchetypeModel, and RiskEngine in `aker_core.ports` so core workflows depend on contracts rather than concrete implementations.

#### Scenario: Port Defines Required Methods
- **WHEN** a developer inspects `MarketScorer`
- **THEN** the interface SHALL document required inputs and outputs for scoring markets

### Requirement: Plugin Registry
The system SHALL provide a registry in `aker_core.plugins` that supports registering adapters by name, retrieving them, and discovering entry-point declared plugins at startup.

#### Scenario: Register And Retrieve Adapter
- **WHEN** `plugins.register("census_acs", CensusACSConnector)` is called
- **THEN** `plugins.get("census_acs")()` SHALL return an instance of `CensusACSConnector`

#### Scenario: Entry Point Discovery Loads Plugins
- **WHEN** plugins are declared via Python entry points
- **THEN** `plugins.discover()` SHALL load and register each adapter without code changes

### Requirement: Testability Through Hot Swapping
Adapters SHALL be hot-swappable in tests by registering test doubles without mutating production wiring.

#### Scenario: Test Registers Stub Adapter
- **WHEN** a test registers a stub with `plugins.register("census_acs", StubConnector, override=True)`
- **THEN** subsequent calls to `plugins.get("census_acs")()` SHALL return the stub implementation for the duration of the test

### Requirement: Flow Orchestration
Prefect deployments SHALL be defined using supported APIs (Prefect 3 `flow.deploy()` / `flow.serve()`) and tested for serialization.

#### Scenario: Deployment Definitions Load
- **WHEN** deployments are instantiated in tests
- **THEN** each deployment SHALL expose a serializable representation without raising exceptions

### Requirement: Structured Logging
The system SHALL expose a typed `aker_core.logging.get_logger(__name__)` returning a structured logger that emits JSON events with contextual fields (e.g., `msa`, `ms`) for traceable operations **and SHALL provide Prometheus helpers (`generate_metrics`, `make_metrics_app`, `start_metrics_server`) with documented behaviour.**

#### Scenario: Market Scoring Log Includes Context
- **WHEN** `get_logger("scoring").info("scored_market", msa="DEN", ms=42)` is called
- **THEN** the emitted log SHALL be JSON containing the event name `scored_market` and the fields `msa` and `ms`

#### Scenario: Logging Helpers Support Prometheus Endpoints
- **WHEN** `generate_metrics()` or `make_metrics_app()` is invoked in an environment with Prometheus client
- **THEN** the helper SHALL return exposition content without repeated registry creation and SHALL raise a clear error if Prometheus is unavailable

### Requirement: Prometheus Metrics Integration
The system MUST support optional Prometheus metrics collection with counters and histograms.

#### Scenario: Counter metrics
- **WHEN** operations complete
- **THEN** appropriate counters are incremented with relevant labels

#### Scenario: Histogram metrics for timing
- **WHEN** timed operations complete
- **THEN** duration histograms record the timing with appropriate buckets

#### Scenario: Metrics endpoint
- **WHEN** Prometheus scrapes the /metrics endpoint
- **THEN** it receives properly formatted metrics in exposition format

### Requirement: Market Score Composer
The system MUST provide a deterministic market score composer that combines pillar scores using documented weights and persists both 0–5 and 0–100 variants.

#### Scenario: Standard Weight Composition
- **WHEN** `markets.score(msa_id|msa_geo, as_of)` is executed with available pillar scores
- **THEN** the composer SHALL apply the standard weighting: 0.3×Supply + 0.3×Jobs + 0.2×Urban + 0.2×Outdoors
- **AND** yield both 0–5 and 0–100 composite scores persisted to `pillar_scores`
- **AND** missing pillars SHALL trigger validation errors rather than silent defaults

#### Scenario: Flexible Input Types
- **WHEN** calling the composer with different input types
- **THEN** it SHALL accept both MSA identifiers (strings) and geometries (Point/Polygon)
- **AND** resolve MSA boundaries for geographic inputs
- **AND** provide consistent scoring regardless of input type

#### Scenario: Deterministic Output
- **WHEN** the composer runs with identical pillar inputs
- **THEN** the resulting composite scores SHALL be deterministic and reproducible
- **AND** enable golden regression tests with fixed inputs
- **AND** support exact comparison of results across environments

#### Scenario: Configurable Weight Overrides
- **WHEN** pillar weights are overridden for scenario analysis
- **THEN** the composer SHALL accept custom weight dictionaries
- **AND** normalise weights to ensure they sum to 1.0
- **AND** track override metadata in persistence and lineage

#### Scenario: Pillar Weight Swap Testing
- **WHEN** testing pillar weight sensitivity
- **THEN** swapping weights (e.g., Supply vs Jobs) SHALL produce predictable score changes
- **AND** maintain mathematical consistency in weight application
- **AND** support regression tests for weight sensitivity analysis

#### Scenario: Persistence and Audit Trail
- **WHEN** composite scores are written to `pillar_scores`
- **THEN** the record SHALL include both 0–5 and 0–100 composite scores
- **AND** pillar breakdown scores for transparency
- **AND** weight scheme metadata and run identifier for auditability
- **AND** link to the `runs` table for complete lineage tracking

#### Scenario: Error Handling and Validation
- **WHEN** insufficient pillar data is available
- **THEN** the composer SHALL raise descriptive validation errors
- **AND** indicate which pillars are missing
- **AND** suggest potential data sources for missing pillars

#### Scenario: Performance and Scalability
- **WHEN** computing scores for multiple MSAs
- **THEN** the composer SHALL handle batch processing efficiently
- **AND** cache intermediate calculations where appropriate
- **AND** provide progress tracking for large-scale operations

### Requirement: Unified Data Validation Stack
The system SHALL standardise on a layered validation stack composed of Pydantic (configuration/runtime DTOs), Pandera (DataFrame and table schemas), and Marshmallow (external payload serialization) while removing the project’s dependence on Great Expectations.

#### Scenario: Pandera Guards Tabular Pipelines
- **WHEN** an ETL flow materialises a DataFrame destined for storage or downstream scoring
- **THEN** the flow SHALL invoke a Pandera schema that enforces column presence, dtypes, and business rule bounds equivalent to the prior Great Expectations suite before persisting or handing off the data

#### Scenario: Pydantic Protects Configuration and Runtime Contracts
- **WHEN** configuration objects or in-memory DTOs are created inside pipelines or services
- **THEN** they SHALL be defined and validated with Pydantic models, raising structured errors on contract violations without requiring Great Expectations wrappers

#### Scenario: Marshmallow Validates External Interfaces
- **WHEN** data is serialised to or from external APIs, files, or analyst-facing exports
- **THEN** Marshmallow schemas SHALL validate and serialise the payloads, replacing Great Expectations-driven serialization checks while preserving audit logs

#### Scenario: Great Expectations Dependency Removed
- **WHEN** the project dependencies and CI workflows are evaluated
- **THEN** Great Expectations SHALL no longer be required or invoked, and validation coverage SHALL be demonstrated via Pydantic, Pandera, and Marshmallow backed tests and documentation

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

### Requirement: State Rule Packs Engine
The system SHALL provide a state-specific rule pack engine that applies location-based defaults, perils, winterization cost adders, and tax cadences with particular emphasis on CO/UT/ID operational characteristics.

#### Scenario: Colorado State Pack Application
- **GIVEN** a Colorado market context with aerospace/tech/health industry anchors
- **WHEN** `state_packs.apply("CO", context)` is called
- **THEN** the system SHALL apply CO-specific defaults including hail/wildfire insurance patterns
- **AND** entitlement variance adjustments SHALL be applied to guardrails
- **AND** winterization cost adders SHALL account for hail exposure and severe weather patterns

#### Scenario: Utah State Pack Application
- **GIVEN** a Utah market context with topography-driven supply constraints
- **WHEN** `state_packs.apply("UT", context)` is called
- **THEN** the system SHALL apply UT-specific topography friction adjustments
- **AND** water rights and winter timing considerations SHALL modify tax cadence
- **AND** higher-ed and tech anchor effects SHALL adjust risk premiums

#### Scenario: Idaho State Pack Application
- **GIVEN** an Idaho market context with in-migration and forest-interface wildfire risks
- **WHEN** `state_packs.apply("ID", context)` is called
- **THEN** the system SHALL apply ID-specific migration pattern adjustments
- **AND** forest-interface wildfire risk multipliers SHALL be applied
- **AND** walkable district development patterns SHALL influence supply constraints

#### Scenario: State Rule Pack Persistence
- **GIVEN** a state rule pack application
- **WHEN** the rule pack is applied to a context
- **THEN** the `state_rules` table SHALL store a snapshot of applied rules
- **AND** the snapshot SHALL include rule version, application timestamp, and affected parameters
- **AND** YAML configuration changes SHALL trigger new snapshots

#### Scenario: UI State Selector Integration
- **GIVEN** a user interface for market analysis
- **WHEN** a state is selected from CO/UT/ID dropdown
- **THEN** the system SHALL automatically pre-fill guardrails based on state rule pack
- **AND** risk cost calculations SHALL reflect state-specific peril patterns
- **AND** winterization cost estimates SHALL include state-specific adders

#### Scenario: State Rule Pack Validation
- **GIVEN** an applied state rule pack
- **WHEN** validation tests are executed
- **THEN** the system SHALL verify that guardrails are mutated as expected
- **AND** risk costs SHALL reflect state-specific peril adjustments
- **AND** tax cadence SHALL align with state-specific requirements
- **AND** winterization cost adders SHALL match state operational notes

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

### Requirement: Robust Normalization Mathematical Foundation
The system SHALL provide a `robust_minmax()` function in `aker_core.scoring` that implements winsorized robust min-max normalization with mathematically proven properties for transforming raw market metrics to standardized 0-100 scores.

#### Scenario: Winsorized Robust Min-Max Algorithm
- **GIVEN** an array of raw metric values with potential outliers
- **WHEN** `scoring.robust_minmax(array, p_low=0.05, p_high=0.95)` is called
- **THEN** the function SHALL calculate the 5th and 95th percentiles as robust bounds
- **AND** apply winsorization by clipping values outside these bounds
- **AND** perform min-max normalization: `100 * (x - min_bound) / (max_bound - min_bound)`
- **AND** return a numpy array with values in the range [0, 100]

#### Scenario: Monotonicity Preservation (Mathematical Property)
- **GIVEN** any two input arrays where `x[i] ≤ y[i]` for all indices i
- **WHEN** both arrays are normalized using `robust_minmax()` with identical parameters
- **THEN** the normalized values SHALL maintain the same order: `result_x[i] ≤ result_y[i]` for all i
- **AND** this property SHALL hold regardless of the percentile parameters chosen
- **AND** the monotonicity SHALL be preserved even with extreme outliers in the data

#### Scenario: Scaling Invariance (Mathematical Property)
- **GIVEN** an input array and the same array scaled by a positive constant factor c > 0
- **WHEN** both arrays are normalized using `robust_minmax()` with identical parameters
- **THEN** the normalized results SHALL be identical within numerical precision
- **AND** the scaling factor SHALL not affect the relative ordering of normalized values
- **AND** this property SHALL hold for any positive scaling factor

#### Scenario: Bounds Guarantee (Mathematical Property)
- **GIVEN** any valid input array (non-empty, contains at least one finite numeric value)
- **WHEN** the array is normalized using `robust_minmax()`
- **THEN** all output values SHALL be in the closed interval [0, 100]
- **AND** the minimum output value SHALL be ≥ 0
- **AND** the maximum output value SHALL be ≤ 100
- **AND** this guarantee SHALL hold for all valid percentile parameter combinations

#### Scenario: Configurable Percentile Parameters
- **GIVEN** different robustness requirements for outlier handling
- **WHEN** `robust_minmax()` is called with custom percentile parameters
- **THEN** the function SHALL accept `p_low` and `p_high` parameters in range [0, 1]
- **AND** validate that `p_low < p_high` with appropriate error messages
- **AND** use default values of `p_low=0.05` and `p_high=0.95` when not specified
- **AND** support different robustness levels for different market characteristics

#### Scenario: Comprehensive Input Validation
- **GIVEN** various types of input data and parameters
- **WHEN** `robust_minmax()` is called
- **THEN** the function SHALL validate that input is a numpy array or array-like
- **AND** check that percentile parameters are valid floats in [0, 1] range
- **AND** ensure `p_low < p_high` with clear error messages
- **AND** handle edge cases gracefully with informative error messages

#### Scenario: Edge Case Handling and Robustness
- **GIVEN** arrays with extreme characteristics (empty, all NaN, single values, constant values)
- **WHEN** `robust_minmax()` processes these arrays
- **THEN** the function SHALL handle empty arrays with appropriate ValueError
- **AND** handle arrays with all NaN values with informative error messages
- **AND** handle single-value arrays by returning appropriate normalized results
- **AND** handle constant arrays by returning the midpoint (50.0) value

#### Scenario: Numerical Stability and Precision
- **GIVEN** arrays with extreme value ranges or precision requirements
- **WHEN** `robust_minmax()` performs calculations
- **THEN** the function SHALL maintain numerical stability across different value ranges
- **AND** use appropriate floating-point precision for financial calculations
- **AND** handle very small differences between min and max bounds
- **AND** provide consistent results across different computing platforms

#### Scenario: Performance Optimization for Large Datasets
- **GIVEN** large arrays representing market data for multiple MSAs
- **WHEN** `robust_minmax()` processes these arrays
- **THEN** the function SHALL use vectorized NumPy operations for efficiency
- **AND** minimize memory allocations and copies
- **AND** support batch processing of multiple arrays
- **AND** maintain performance characteristics suitable for real-time scoring

#### Scenario: Integration with Scoring Pipeline
- **GIVEN** normalized output from `robust_minmax()` and pillar aggregation functions
- **WHEN** the normalized values are used in the scoring pipeline
- **THEN** the normalized values SHALL be directly compatible with `pillar_score()` functions
- **AND** support both individual array normalization and batch processing
- **AND** integrate seamlessly with the complete scoring workflow from raw metrics to final scores

#### Scenario: Mathematical Correctness Validation
- **GIVEN** the mathematical properties and edge cases
- **WHEN** comprehensive testing is performed
- **THEN** all three core properties (monotonicity, scaling invariance, bounds) SHALL be validated
- **AND** edge cases SHALL be handled appropriately without violating mathematical guarantees
- **AND** numerical stability SHALL be maintained across different data distributions
- **AND** the implementation SHALL match the specification in project.md exactly

#### Scenario: Documentation and Mathematical Proofs
- **GIVEN** the need for mathematical rigor and developer understanding
- **WHEN** the function is documented and tested
- **THEN** the documentation SHALL include formal mathematical proofs of the three core properties
- **AND** provide clear explanations of the winsorization and normalization algorithms
- **AND** include usage examples demonstrating the mathematical properties
- **AND** provide guidance for selecting appropriate percentile parameters

### Requirement: Core Normalization Properties Are Property-Tested
The scoring utilities SHALL retain property-based tests (Hypothesis or equivalent) that exercise `robust_minmax` over a wide numeric domain, validating bounds, monotonicity, scaling invariance, and NaN propagation so future regressions surface automatically.

#### Scenario: Property Suite Guards Against Regression
- **WHEN** the normalization implementation changes
- **THEN** the Hypothesis suite SHALL run in CI and fail on deviations from the documented invariants (e.g., values escaping [0,100] or scaling invariance breaking)

### Requirement: Lint Surface Remains Actionable
Linting SHALL run clean by default, either because legacy/demo modules conform to style/import rules or are isolated from the production lint config with documented exclusions.

#### Scenario: `ruff check .` Passes Without Demo Noise
- **WHEN** contributors run `ruff check .`
- **THEN** the command SHALL complete without raising errors from demo scripts or migrations, ensuring lint failures indicate actionable regressions

### Requirement: Geospatial Validation Alignment
The data lake SHALL interpret geometry and CRS validation results using the new Pandera-backed helper outputs so that valid datasets are not misclassified and warnings remain actionable.

#### Scenario: Valid GeoDataFrame Persists Without False Warnings
- **GIVEN** a GeoDataFrame whose geometries are valid and whose CRS matches UI or storage expectations
- **WHEN** `DataLake.write` persists the dataset with geometry columns
- **THEN** geometry validation SHALL not raise exceptions or emit warnings, and the partition path SHALL be returned

#### Scenario: Invalid Geometry Surfaces Detailed Warning
- **GIVEN** a GeoDataFrame containing an invalid geometry
- **WHEN** `DataLake.write` runs validation
- **THEN** the logger SHALL include the offending index and Shapely `explain_validity` message sourced from `GeometryValidationResult`

#### Scenario: CRS Validation Uses Compatibility Flags
- **GIVEN** a GeoDataFrame whose CRS metadata is missing or mismatched
- **WHEN** `DataLake.write` inspects the `validate_crs` response
- **THEN** the warning SHALL be driven by `has_crs`, `is_storage_crs`, `is_ui_crs`, or `detected_crs` fields rather than relying on a removed `crs_compatible` value

### Requirement: Supply ETL Error Simulation Integrity
The supply ETL test harness SHALL import the HTTP error type it raises so failure branches are exercised and regressions surface during testing.

#### Scenario: Dummy Response Raises HTTPError With Imported Type
- **WHEN** the test client triggers a >=400 status in `DummyResponse.raise_for_status`
- **THEN** a `requests.HTTPError` SHALL be raised without NameError, allowing the failure branch assertion to execute

### Requirement: Governance Package Lint Compliance
The governance module and its associated tests SHALL pass default linting rules (import order, unused symbol elimination) so that `ruff check .` can be relied on for regressions without local overrides.

#### Scenario: Governance Imports Organized
- **WHEN** `ruff check` runs against `src/aker_core/governance` and governance-related tests
- **THEN** it SHALL succeed without unsorted-import (`I001`) or unused-import (`F401`) reports.

### Requirement: Demo/Test Isolation Strategy Documented
Legacy governance demos or long-running scripts SHALL either comply with lint rules or live in a clearly documented location that is excluded from production linting, preventing continuous baseline noise.

#### Scenario: Lint Baseline Remains Clean After Demo Changes
- **WHEN** a new developer runs `ruff check .`
- **THEN** governance-related demo/test files SHALL not introduce non-actionable lint failures because they are either clean or explicitly excluded with justification in the lint configuration.

