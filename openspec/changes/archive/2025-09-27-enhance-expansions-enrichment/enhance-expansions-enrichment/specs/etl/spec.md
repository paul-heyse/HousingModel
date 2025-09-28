## MODIFIED Requirements
### Requirement: Named Entity Recognition for Expansion Data
The system MUST extract structured expansion data using NLP-driven entity recognition, including configurable model patterns for company, location, industry, and investment entities, and SHALL enrich entity results with geocoding lookups and confidence scores.

#### Scenario: Company Name Extraction
- **WHEN** processing expansion announcements
- **THEN** the ingestor applies custom NER pipelines (e.g., spaCy patterns) to identify company/organization names
- **AND** normalises the entity using configured registries
- **AND** records an entity confidence score alongside the canonical name

#### Scenario: Location and Geographic Data
- **WHEN** processing location information
- **THEN** the system geocodes detected places to return city, state, country, and lat/long attributes
- **AND** caches geocoding responses to reduce external lookups
- **AND** raises review flags if no confidence threshold is met or ambiguous locations are detected

#### Scenario: Job Count and Expansion Details
- **WHEN** processing expansion announcements
- **THEN** the system extracts job creation numbers, investment amounts, and facility timelines
- **AND** classifies industry sector and event type using enriched taxonomies
- **AND** stores extraction provenance to support manual review

### Requirement: Expansion Event Data Model
The system MUST provide a standardized data model for expansion events that captures enriched geographic, industry, and confidence metadata needed for downstream analysis and review workflows.

#### Scenario: Structured Expansion Data
- **WHEN** `ExpansionsIngestor.scan(feeds)` returns results
- **THEN** it returns `[ExpansionEvent]` containing company, location, jobs, timeline, investment, industry, geocode coordinates, and source metadata
- **AND** each field includes extraction and geocoding confidence scores
- **AND** events record anomaly flags for downstream analytics

#### Scenario: Event Classification
- **WHEN** processing announcements
- **THEN** the system classifies events by type (new facility, expansion, relocation) and industry sector using enriched dictionaries
- **AND** records whether the classification passed confidence thresholds or requires review
- **AND** tags events with custom labels (e.g., relocation, headquarters) derived from NLP features

#### Scenario: Data Enrichment
- **WHEN** creating expansion events
- **THEN** the system enriches events with geographic and market context, including linkage to known companies and historical expansion activity
- **AND** stores z-score or percentile metrics for jobs/investment to support anomaly detection
- **AND** ensures enriched attributes remain auditable via metadata provenance

### Requirement: Monitoring and Alerting
The system MUST provide monitoring and alerting for data collection health with structured metrics, logs, and persistence of per-run telemetry.

#### Scenario: Processing Success Monitoring
- **WHEN** content processing completes
- **THEN** the ingestor emits Prometheus metrics for processed articles, emitted events, review queue counts, and errors
- **AND** logs structured events summarising per-feed success/failure counts
- **AND** persists run-level metrics for later dashboarding

#### Scenario: Data Freshness Monitoring
- **WHEN** monitoring data pipeline health
- **THEN** feed freshness, retry counts, and error budgets are tracked and compared against alert thresholds
- **AND** stale or failing feeds generate structured alerts for operators
- **AND** monitoring artefacts are available through Prefect run metadata

#### Scenario: Quality Metrics
- **WHEN** evaluating extraction quality
- **THEN** the system records precision/recall metrics for NER, anomaly flags, and review queue trends
- **AND** exposes these metrics through dashboards or logs for iterative improvement
- **AND** highlights recurring failure reasons for rule tuning

## ADDED Requirements
### Requirement: Historical Benchmarking and Anomaly Detection
The system SHALL benchmark extracted expansion metrics against historical distributions and flag anomalous announcements for analyst review.

#### Scenario: Outlier Detection
- **WHEN** jobs or investment figures exceed configured z-score or percentile thresholds for the relevant sector/region
- **THEN** the event is marked as an anomaly with supporting context (baseline, z-score)
- **AND** the event is automatically placed in the review queue with an explicit reason code

#### Scenario: Benchmark Maintenance
- **WHEN** new expansion events are persisted
- **THEN** historical aggregates roll forward to incorporate the latest data while retaining prior baselines for comparison
- **AND** the system supports sector- and geography-specific thresholds configurable via settings

#### Scenario: Analyst Visibility
- **WHEN** analysts inspect the review queue snapshot
- **THEN** anomaly reason codes and benchmark metrics are surfaced to prioritise manual action
- **AND** exported review artefacts include raw and enriched values for validation
