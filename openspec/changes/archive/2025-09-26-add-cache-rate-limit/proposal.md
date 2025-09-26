## Why
External data dependencies (GTFS, OSM, EPA APIs) require robust caching and rate limiting to ensure reliable pipeline execution, prevent API quota exhaustion, and enable offline operation. This enables cost-effective, resilient data pipelines with proper HTTP compliance and lineage tracking.

## What Changes
- Introduce `aker_core.cache` module with intelligent HTTP caching supporting ETag/Last-Modified headers.
- Implement `RateLimiter` class with exponential backoff, jitter, and token bucket algorithm.
- Add local storage for Parquet, GTFS, and OSM data with TTL-based expiration.
- Integrate with lineage tracking to log cache hits/misses and rate limit events.
- Provide offline mode capability for end-to-end pipeline execution.

## Impact
- Affected specs: core/cache
- Affected code: `src/aker_core/cache.py`, data ingestion modules, HTTP clients, lineage tracking.
