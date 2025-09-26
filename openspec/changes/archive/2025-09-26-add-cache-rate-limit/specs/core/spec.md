## ADDED Requirements
### Requirement: HTTP Response Caching
The system MUST provide intelligent HTTP caching with ETag and Last-Modified header support for external data sources.

#### Scenario: Cache hit with ETag
- **WHEN** a URL is requested with a cached ETag response
- **AND** the server returns 304 Not Modified
- **THEN** the cached response is returned without re-downloading

#### Scenario: Cache miss with fresh data
- **WHEN** a URL is requested and cache is stale or missing
- **AND** the server returns new data
- **THEN** the response is cached with new ETag/Last-Modified headers

#### Scenario: TTL-based expiration
- **WHEN** cache entries exceed their TTL
- **THEN** they are considered stale and trigger fresh requests

### Requirement: Rate Limiting with Backoff
The system MUST implement rate limiting with exponential backoff and jitter to prevent API quota exhaustion.

#### Scenario: Rate limit exceeded
- **WHEN** an API rate limit is hit
- **THEN** exponential backoff with jitter is applied before retry

#### Scenario: Token bucket rate limiting
- **WHEN** using RateLimiter(token="epa_airnow")
- **THEN** requests are limited according to the configured token bucket parameters

#### Scenario: Rate limit event logging
- **WHEN** rate limiting occurs
- **THEN** the event is logged to lineage with timing and retry information

### Requirement: Local Data Storage
The system MUST provide local storage for Parquet, GTFS, and OSM data with proper organization.

#### Scenario: Parquet data storage
- **WHEN** writing processed data to cache
- **THEN** it is stored in /data/parquet/{dataset}/ with appropriate partitioning

#### Scenario: GTFS/OSM file storage
- **WHEN** downloading GTFS or OSM data
- **THEN** it is stored in /data/gtfs/ or /data/osm/ with metadata tracking

#### Scenario: Cache lineage integration
- **WHEN** cache operations occur
- **THEN** hits, misses, and storage events are logged to the lineage table

### Requirement: Offline Mode Capability
The system MUST support end-to-end pipeline execution in offline mode with network disabled.

#### Scenario: Offline pipeline execution
- **WHEN** network connectivity is disabled
- **AND** all required data is cached locally
- **THEN** the pipeline executes successfully using cached data

#### Scenario: Cache miss in offline mode
- **WHEN** network connectivity is disabled
- **AND** required data is not cached
- **THEN** the pipeline fails gracefully with clear error messaging
