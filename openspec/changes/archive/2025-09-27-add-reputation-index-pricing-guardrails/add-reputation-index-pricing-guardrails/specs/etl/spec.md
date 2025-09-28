## ADDED Requirements

### Requirement: Reviews & NPS ETL Connectors
The system SHALL provide connectors to ingest reviews and NPS suitable for Reputation Index.

#### Scenario: Reviews ingestion
- **WHEN** fetching reviews from APIs (e.g., Google Business Profile, Yelp Fusion, App Store/Play Store)
- **THEN** the ETL SHALL normalise fields (rating, text, date, source, location) with lineage

#### Scenario: NPS ingestion
- **WHEN** fetching NPS from survey platforms (e.g., Delighted, Qualtrics, Medallia)
- **THEN** the ETL SHALL normalise scores and sampling windows and store response counts

#### Scenario: Benchmarks enrichment (optional)
- **WHEN** integrating market/brand benchmarks (e.g., J.D. Power, industry reports)
- **THEN** the ETL SHALL provide reference distributions for calibration

#### Scenario: Data quality
- **WHEN** ETL completes
- **THEN** outputs SHALL include source, version, extract time, and validation results

