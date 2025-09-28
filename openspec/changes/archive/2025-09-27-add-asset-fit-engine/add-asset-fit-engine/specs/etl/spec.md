## ADDED Requirements

### Requirement: Asset Fit ETL Connectors
The system SHALL provide ETL connectors to source attributes and context needed for fit evaluation and store standardized records for scoring.

#### Scenario: Asset attributes ingestion
- **WHEN** extracting asset attributes (product type, year built, unit mix, sizes, ceiling heights, W/D)
- **THEN** the ETL SHALL normalize fields and map to canonical schema with data lineage

#### Scenario: Parking, transit, and context enrichment
- **WHEN** enriching with parking inventory, stall types, and proximity to high‑frequency transit
- **THEN** the ETL SHALL compute context labels (e.g., transit‑rich, urban core) used by parking guardrails

#### Scenario: Regulatory minimums and local ordinances
- **WHEN** importing jurisdictional requirements (parking minimums/maximums, W/D restrictions, accessibility)
- **THEN** the ETL SHALL produce normalized rules tied to geographies and effective dates

#### Scenario: Market comparator datasets
- **WHEN** integrating comps (by product type and vintage) for benchmark distributions
- **THEN** the ETL SHALL compute reference ranges for unit sizes and mixes to inform soft guardrails

#### Scenario: Persistence and auditability
- **WHEN** ETL completes
- **THEN** records SHALL include source, version, extract time, and quality checks outcomes


