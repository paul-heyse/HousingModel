"""Metrics helpers for expansion ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from aker_core.logging import increment_counter, observe_duration


@dataclass
class IngestionMetrics:
    labels: Dict[str, str] = field(default_factory=dict)
    events_processed: int = 0
    events_emitted: int = 0
    review_count: int = 0
    anomalies: int = 0
    feed_errors: int = 0
    _start_time_ms: float = 0.0
    duration_ms: float = 0.0

    def record_start(self) -> None:
        import time

        self._start_time_ms = time.perf_counter() * 1000

    def record_event_processed(self) -> None:
        self.events_processed += 1

    def record_event_emitted(self) -> None:
        self.events_emitted += 1

    def record_review_queue(self) -> None:
        self.review_count += 1

    def record_anomaly(self) -> None:
        self.anomalies += 1

    def record_feed_error(self) -> None:
        self.feed_errors += 1

    def emit(self) -> None:
        duration_ms = 0.0
        if self._start_time_ms:
            import time

            duration_ms = time.perf_counter() * 1000 - self._start_time_ms
            self.duration_ms = duration_ms
            observe_duration(
                "expansion_ingest_duration_seconds",
                "Time to process expansion feeds",
                duration_ms / 1000.0,
                **self.labels,
            )

        increment_counter(
            "expansion_events_processed_total",
            "Expansion articles processed",
            amount=self.events_processed,
            **self.labels,
        )
        if self.events_emitted:
            increment_counter(
                "expansion_events_emitted_total",
                "Expansion events emitted",
                amount=self.events_emitted,
                **self.labels,
            )
        if self.review_count:
            increment_counter(
                "expansion_events_review_total",
                "Expansion events queued for review",
                amount=self.review_count,
                **self.labels,
            )
        if self.anomalies:
            increment_counter(
                "expansion_events_anomalies_total",
                "Expansion events flagged as anomalies",
                amount=self.anomalies,
                **self.labels,
            )
        if self.feed_errors:
            increment_counter(
                "expansion_events_feed_errors_total",
                "Feed errors encountered",
                amount=self.feed_errors,
                **self.labels,
            )

    def as_dict(self) -> Dict[str, float]:
        return {
            "events_processed": float(self.events_processed),
            "events_emitted": float(self.events_emitted),
            "review_count": float(self.review_count),
            "anomalies": float(self.anomalies),
            "feed_errors": float(self.feed_errors),
            "duration_ms": float(self.duration_ms),
            "timestamp": datetime.utcnow().isoformat(),
        }


__all__ = ["IngestionMetrics"]
