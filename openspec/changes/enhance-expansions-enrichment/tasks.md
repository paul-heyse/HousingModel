## 1. Enrichment Engine
- [ ] 1.1 Integrate lightweight NLP/NER (e.g. spaCy custom patterns) for company and location extraction.
- [ ] 1.2 Implement configurable geocoding lookup with caching and attach lat/long plus match confidence to events.
- [ ] 1.3 Extend industry and event-type classification using enriched taxonomies and historic company metadata.

## 2. Anomaly Detection & Review
- [ ] 2.1 Capture historical statistics (jobs, investment) and compute z-score/outlier flags per sector and region.
- [ ] 2.2 Auto-route anomalous or low-confidence events into the review queue with explicit reason codes.
- [ ] 2.3 Persist review queue snapshots (Parquet/CSV) and expose convenience access for analyst workflows.

## 3. Monitoring & Observability
- [ ] 3.1 Publish Prometheus metrics (feed successes, failures, review counts, processing latency) and structured logs.
- [ ] 3.2 Track feed freshness, retries, and error budgets; raise alerts/logs when thresholds are breached.
- [ ] 3.3 Persist per-run ingestion metrics to the data lake for dashboarding.

## 4. Integration & Tests
- [ ] 4.1 Wire enriched events and metrics into Prefect flow execution and run metadata/lineage.
- [ ] 4.2 Add comprehensive tests covering NER accuracy, geocoding fallback, anomaly detection, and metrics emission.
- [ ] 4.3 Update documentation and configuration samples to reflect new enrichment and monitoring capabilities.
