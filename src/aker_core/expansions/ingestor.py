"""Ingestion utilities for economic expansion announcements."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

import feedparser
import pandas as pd
from bs4 import BeautifulSoup

from aker_data.lake import DataLake

from .anomaly import AnomalyDetector
from .entities import EntityExtractionResult, EntityExtractor
from .geocode import BaseGeocoder, GeocodeResult, StaticGeocoder
from .metrics import IngestionMetrics
from .models import ExpansionEvent

LOGGER = logging.getLogger(__name__)

_KEYWORD_DEFAULTS = [
    "expansion",
    "expands",
    "new facility",
    "jobs",
    "investment",
    "hiring",
    "manufacturing plant",
    "headquarters",
]


@dataclass(slots=True)
class FeedConfig:
    """Simple configuration structure for RSS feed inputs."""

    url: str
    label: str
    enabled: bool = True
    parser_hint: Optional[str] = None


@dataclass
class ReviewItem:
    """Container describing an event queued for manual review."""

    event: ExpansionEvent
    reasons: List[str] = field(default_factory=list)


class ReviewQueue:
    """Accumulates low-confidence events for manual inspection."""

    def __init__(self) -> None:
        self._items: List[ReviewItem] = []

    def enqueue(self, event: ExpansionEvent, reasons: Iterable[str]) -> None:
        reason_list = [r for r in reasons if r]
        self._items.append(ReviewItem(event=event, reasons=reason_list))

    @property
    def items(self) -> List[ReviewItem]:
        return list(self._items)

    def to_dataframe(self) -> pd.DataFrame:
        if not self._items:
            return pd.DataFrame(columns=["company", "confidence", "reasons", "source_url"])
        records = [
            {
                "company": item.event.company,
                "confidence": item.event.confidence,
                "reasons": "; ".join(item.reasons),
                "source_url": item.event.source_url,
                "publication_date": item.event.publication_date,
                "state": item.event.state,
                "industry": item.event.industry,
                "jobs_created": item.event.jobs_created,
                "investment_amount": item.event.investment_amount,
                "anomaly_flags": "; ".join(item.event.anomaly_flags or []),
            }
            for item in self._items
        ]
        return pd.DataFrame.from_records(records)

    def render_console(self) -> str:
        if not self._items:
            return "No items queued for review."
        lines = ["Queued expansion events requiring manual review:"]
        for idx, item in enumerate(self._items, start=1):
            lines.append(
                f"{idx}. {item.event.company} ({item.event.confidence:.2f}) -> {', '.join(item.reasons)}"
            )
        return "\n".join(lines)


class ExpansionsIngestor:
    """Collects and enriches economic expansion announcements from RSS feeds."""

    def __init__(
        self,
        feeds: Optional[Sequence[FeedConfig]] = None,
        keywords: Optional[Sequence[str]] = None,
        confidence_threshold: float = 0.65,
        entity_extractor: Optional[EntityExtractor] = None,
        geocoder: Optional[BaseGeocoder] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ) -> None:
        self.feeds = list(feeds or [])
        self.keywords = [kw.lower() for kw in (keywords or _KEYWORD_DEFAULTS)]
        self.confidence_threshold = confidence_threshold
        self.review_queue = ReviewQueue()
        self.metrics = IngestionMetrics()
        self._entity_extractor = entity_extractor or EntityExtractor()
        self._geocoder = geocoder or StaticGeocoder(
            {("boulder", "co"): (40.01499, -105.27055), ("denver", "co"): (39.7392, -104.9903)}
        )
        self._anomaly_detector = anomaly_detector

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def scan(self, feeds: Optional[Sequence[FeedConfig]] = None) -> List[ExpansionEvent]:
        feed_configs = list(feeds or self.feeds)
        if not feed_configs:
            raise ValueError("No feed configuration supplied")

        events: List[ExpansionEvent] = []
        self.metrics.record_start()

        for cfg in feed_configs:
            if not cfg.enabled:
                continue
            try:
                parsed = feedparser.parse(cfg.url)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Failed to parse feed %s: %s", cfg.url, exc)
                self.metrics.record_feed_error()
                continue

            for entry in parsed.entries:
                self.metrics.record_event_processed()

                article_text, summary = self._extract_text(entry, cfg.parser_hint)
                if not article_text and not summary:
                    continue

                combined_text = " ".join(
                    filter(
                        None,
                        [
                            getattr(entry, "title", ""),
                            summary,
                            article_text,
                            getattr(entry, "link", ""),
                        ],
                    )
                )

                extraction = self._entity_extractor.extract(article_text, summary)
                if not self._looks_like_expansion(combined_text) and not self._has_minimum_signal(
                    extraction, article_text
                ):
                    continue

                geocode = self._geocoder.geocode(
                    extraction.location.get("city"),
                    extraction.location.get("state"),
                    extraction.location.get("country"),
                )
                event = self._build_event(cfg, entry, article_text, summary, extraction, geocode)
                event = self._apply_anomaly_detection(event)

                if self._validate_event(event):
                    events.append(event)
                    self.metrics.record_event_emitted()

        self.metrics.emit()
        return events

    def persist_events(
        self,
        lake: DataLake,
        events: Sequence[ExpansionEvent],
        *,
        as_of: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
    ) -> Optional[str]:
        if not events:
            return None
        as_of_value = as_of or datetime.utcnow().strftime("%Y-%m")
        df = pd.DataFrame([event.model_dump() for event in events])
        if "anomaly_score" in df.columns:
            df["anomaly_score"] = df["anomaly_score"].apply(
                lambda payload: json.dumps(payload) if payload else None
            )
        if "anomaly_flags" in df.columns:
            df["anomaly_flags"] = df["anomaly_flags"].apply(
                lambda flags: ",".join(flags) if isinstance(flags, list) and flags else None
            )
        return lake.write(
            df, dataset="expansion_events", as_of=as_of_value, partition_by=partition_by
        )

    def persist_review_queue(
        self,
        lake: DataLake,
        *,
        as_of: Optional[str] = None,
    ) -> Optional[str]:
        if not self.review_queue.items:
            return None
        df = self.review_queue.to_dataframe()
        if df.empty:
            return None
        as_of_value = as_of or datetime.utcnow().strftime("%Y-%m")
        return lake.write(df, dataset="expansion_events_review_queue", as_of=as_of_value)

    def persist_metrics(
        self,
        lake: DataLake,
        *,
        as_of: Optional[str] = None,
    ) -> Optional[str]:
        df = pd.DataFrame([self.metrics.as_dict()])
        as_of_value = as_of or datetime.utcnow().strftime("%Y-%m")
        return lake.write(df, dataset="expansion_events_metrics", as_of=as_of_value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_event(
        self,
        feed_cfg: FeedConfig,
        entry: Any,
        article_text: str,
        summary: str,
        extraction: EntityExtractionResult,
        geocode: GeocodeResult,
    ) -> ExpansionEvent:
        publication = self._parse_publication_date(entry)
        metadata = {
            "feed_label": feed_cfg.label,
            "guid": getattr(entry, "id", None),
            "title": getattr(entry, "title", ""),
        }

        jobs = self._extract_jobs(article_text)
        investment = self._extract_investment(article_text)
        event_type = self._classify_event(article_text)
        timeline = self._extract_timeline(article_text)

        confidence = self._score_event(
            company=extraction.company,
            location=extraction.location,
            jobs=jobs,
        )

        review_reasons: List[str] = []
        if confidence < self.confidence_threshold:
            review_reasons.append(
                f"confidence below threshold ({confidence:.2f} < {self.confidence_threshold:.2f})"
            )
        if jobs is None:
            review_reasons.append("jobs missing")
        if not extraction.location.get("city") and not extraction.location.get("state"):
            review_reasons.append("location missing")
        if geocode.confidence == 0.0:
            review_reasons.append("geocode_confidence_low")

        event = ExpansionEvent(
            company=extraction.company or "Unknown Company",
            summary=summary,
            publication_date=publication,
            source=feed_cfg.label,
            source_url=getattr(entry, "link", ""),
            city=extraction.location.get("city"),
            state=extraction.location.get("state"),
            country=extraction.location.get("country"),
            facility_location=extraction.location.get("raw"),
            latitude=geocode.latitude,
            longitude=geocode.longitude,
            geocode_confidence=geocode.confidence,
            geocode_provider=geocode.provider,
            jobs_created=jobs,
            investment_amount=investment,
            currency="USD" if investment is not None else None,
            event_type=event_type,
            industry=extraction.industry,
            timeline=timeline,
            tags=self._extract_tags(article_text),
            confidence=confidence,
            company_confidence=extraction.company_confidence,
            location_confidence=extraction.location_confidence,
            industry_confidence=extraction.industry_confidence,
            jobs_confidence=1.0 if jobs is not None else 0.0,
            investment_confidence=1.0 if investment is not None else 0.0,
            review_required=bool(review_reasons),
            metadata=metadata,
            raw_text=article_text,
        )

        if review_reasons:
            self.review_queue.enqueue(event, review_reasons)
            self.metrics.record_review_queue()
        return event

    def _apply_anomaly_detection(self, event: ExpansionEvent) -> ExpansionEvent:
        if self._anomaly_detector is None:
            return event
        assessment = self._anomaly_detector.score(event)
        if not assessment.flags:
            return event
        self.metrics.record_anomaly()
        enriched = event.model_copy(
            update={
                "review_required": True,
                "anomaly_score": {
                    "jobs_zscore": assessment.jobs_zscore,
                    "investment_zscore": assessment.investment_zscore,
                },
                "anomaly_flags": assessment.flags,
            }
        )
        return enriched

    def _extract_text(self, entry: Any, parser_hint: Optional[str]) -> tuple[str, str]:
        summary = getattr(entry, "summary", "")
        contents = []
        if hasattr(entry, "content"):
            for content in entry.content:
                contents.append(content.get("value", ""))
        if not contents and summary:
            contents.append(summary)
        if parser_hint == "summary-only":
            contents = [summary]
        text_parts = []
        for html in contents:
            soup = BeautifulSoup(html, "html.parser")
            text_parts.append(soup.get_text(" ", strip=True))
        text = " \n".join([part for part in text_parts if part])
        return text, BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)

    def _looks_like_expansion(self, text: str) -> bool:
        haystack = text.lower()
        return any(keyword in haystack for keyword in self.keywords)

    def _has_minimum_signal(self, extraction: EntityExtractionResult, article_text: str) -> bool:
        if extraction.company:
            return True
        location = extraction.location
        if location.get("city") or location.get("state"):
            return True
        lowered = article_text.lower()
        if any(token in lowered for token in ("expand", "expansion", "jobs", "hiring", "facility")):
            return True
        jobs_hint = self._extract_jobs(article_text)
        return jobs_hint is not None

    def _parse_publication_date(self, entry: Any) -> datetime:
        published = getattr(entry, "published_parsed", None)
        if published:
            return datetime(*published[:6])
        published_text = getattr(entry, "published", None) or getattr(entry, "updated", None)
        if published_text:
            try:
                return datetime.fromisoformat(published_text)
            except ValueError:
                pass
        return datetime.utcnow()

    def _extract_jobs(self, article_text: str) -> Optional[int]:
        match = re.search(
            r"(\d{1,3}(?:,\d{3})*)(?=\s+(?:new\s+)?jobs?)", article_text, flags=re.IGNORECASE
        )
        if not match:
            return None
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            return None

    def _extract_investment(self, article_text: str) -> Optional[float]:
        match = re.search(
            r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(million|billion)?",
            article_text,
            re.IGNORECASE,
        )
        if not match:
            return None
        amount = float(match.group(1).replace(",", ""))
        scale = match.group(2)
        if scale:
            scale = scale.lower()
            if scale == "billion":
                amount *= 1000
        return amount

    def _extract_timeline(self, article_text: str) -> Optional[str]:
        match = re.search(r"(by|in)\s+(Q[1-4]\s+\d{4}|\d{4})", article_text)
        if match:
            return match.group(0)
        return None

    def _extract_tags(self, article_text: str) -> List[str]:
        tags = []
        lowered = article_text.lower()
        if "headquarter" in lowered:
            tags.append("headquarters")
        if "relocat" in lowered:
            tags.append("relocation")
        if "training" in lowered:
            tags.append("workforce")
        return tags

    def _score_event(
        self,
        *,
        company: Optional[str],
        location: Dict[str, Optional[str]],
        jobs: Optional[int],
    ) -> float:
        score = 0.0
        if company:
            score += 0.35
        if location.get("city") or location.get("state"):
            score += 0.35
        if jobs:
            score += 0.2
        if jobs and jobs >= 100:
            score += 0.05
        return min(score, 1.0)

    def _classify_event(self, article_text: str) -> Optional[str]:
        lowered = article_text.lower()
        if "new facility" in lowered or "groundbreaking" in lowered:
            return "new_facility"
        if "expansion" in lowered or "expand" in lowered:
            return "expansion"
        if "relocat" in lowered:
            return "relocation"
        return None

    def _validate_event(self, event: ExpansionEvent) -> bool:
        reasons: List[str] = []
        drop_event = False
        if event.jobs_created is not None and event.jobs_created > 100_000:
            reasons.append("jobs exceeds upper bound")
            drop_event = True
        if event.jobs_created is not None and event.jobs_created == 0:
            reasons.append("jobs equal zero")
            drop_event = True
        if event.investment_amount is not None and event.investment_amount > 10_000:
            reasons.append("investment implausibly large")
            drop_event = True
        if event.anomaly_flags:
            reasons.extend(event.anomaly_flags)
        if reasons:
            self.review_queue.enqueue(event, reasons)
            self.metrics.record_review_queue()
        return not drop_event


__all__ = ["FeedConfig", "ExpansionsIngestor", "ReviewQueue"]
