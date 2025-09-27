## Why
Economic development announcements, particularly job expansions and new facilities, provide critical leading indicators for market growth and innovation activity. However, this information is scattered across press releases, RSS feeds, and news sources with inconsistent formats. A specialized ingestor using natural language processing can automatically extract and structure this valuable market intelligence data.

## What Changes
- Introduce `ExpansionsIngestor` for parsing press releases and RSS feeds for job expansion announcements.
- Implement simple Named Entity Recognition (NER) for extracting company names, locations, job counts, and expansion details.
- Create structured `ExpansionEvent` data model for standardized expansion data.
- Add configurable RSS feed sources and parsing rules for different announcement types.
- Integrate with existing ETL orchestration and data lake storage.

## Impact
- Affected specs: etl/ingestion
- Affected code: `src/aker_core/expansions/`, NLP processing, data lake storage.
