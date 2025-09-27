from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pandas as pd
import pytest

from aker_core.expansions import (
    AnomalyDetector,
    ExpansionsIngestor,
    FeedConfig,
)
from aker_core.expansions.geocode import StaticGeocoder
from aker_data.lake import DataLake


class DummyEntry(SimpleNamespace):
    pass


class DummyFeed:
    def __init__(self, entries: List[DummyEntry]):
        self.entries = entries


@pytest.fixture()
def sample_feed(monkeypatch):
    entry = DummyEntry(
        title="TechCorp announces major expansion",
        summary=(
            "TechCorp will create 450 new jobs with a new manufacturing facility in Boulder, CO."
        ),
        link="https://example.com/techcorp-expansion",
        published="2025-02-18T12:00:00",
        content=[
            {
                "value": "TechCorp announced a $120 million investment to expand operations in Boulder, CO, creating 450 new jobs by 2026."
            }
        ],
        id="abc-123",
    )

    monkeypatch.setattr(
        "aker_core.expansions.ingestor.feedparser.parse",
        lambda url: DummyFeed([entry]),
    )

    return FeedConfig(url="https://example.com/rss", label="test_feed")


def test_ingestor_extracts_company_location_and_jobs(sample_feed):
    geocoder = StaticGeocoder({("boulder", "co"): (40.01499, -105.27055)})
    ingestor = ExpansionsIngestor(feeds=[sample_feed], geocoder=geocoder)
    events = ingestor.scan()

    assert len(events) == 1
    event = events[0]
    assert event.company.startswith("TechCorp")
    assert event.jobs_created == 450
    assert event.state == "CO"
    assert event.city == "Boulder"
    assert event.confidence >= 0.6
    assert event.latitude and event.longitude
    assert event.company_confidence > 0
    assert event.location_confidence > 0
    assert not event.anomaly_flags
    assert not ingestor.review_queue.items  # high confidence should not enqueue review


def test_low_confidence_events_are_queued(monkeypatch):
    entry = DummyEntry(
        title="Regional council highlights upcoming expansion meetup",
        summary="This newsletter highlights a small business meetup with an expansion focus.",
        link="https://example.com/meetup",
        published="2025-02-18T12:00:00",
        content=[{"value": "Entrepreneurs will gather in Denver."}],
        id="def-456",
    )
    monkeypatch.setattr(
        "aker_core.expansions.ingestor.feedparser.parse",
        lambda url: DummyFeed([entry]),
    )
    feed = FeedConfig(url="https://example.com/rss", label="test_feed")
    ingestor = ExpansionsIngestor(feeds=[feed])
    events = ingestor.scan()

    assert events
    assert ingestor.review_queue.items
    report = ingestor.review_queue.render_console()
    assert "Queued expansion events" in report


def test_events_can_be_persisted(tmp_path, sample_feed):
    data_lake = DataLake(base_path=tmp_path)
    ingestor = ExpansionsIngestor(feeds=[sample_feed])
    events = ingestor.scan()

    as_of = "2025-02"
    path = ingestor.persist_events(data_lake, events, as_of=as_of, partition_by=["state"])
    assert path is not None

    dataset_dir = tmp_path / "expansion_events"
    assert dataset_dir.exists()
    parquet_files = list(dataset_dir.rglob("*.parquet"))
    assert parquet_files, "Expected parquet output in the data lake"


def test_review_queue_persistence(tmp_path, monkeypatch):
    entry = DummyEntry(
        title="Regional council highlights upcoming expansion meetup",
        summary="This newsletter highlights a small business meetup with an expansion focus.",
        link="https://example.com/meetup",
        published="2025-02-18T12:00:00",
        content=[{"value": "Entrepreneurs will gather in Denver."}],
        id="ghi-789",
    )
    monkeypatch.setattr(
        "aker_core.expansions.ingestor.feedparser.parse",
        lambda url: DummyFeed([entry]),
    )
    feed = FeedConfig(url="https://example.com/rss", label="test_feed")
    lake = DataLake(base_path=tmp_path)
    ingestor = ExpansionsIngestor(feeds=[feed])
    ingestor.scan()
    review_path = ingestor.persist_review_queue(lake, as_of="2025-03")
    assert review_path is not None
    assert (tmp_path / "expansion_events_review_queue").exists()


def test_anomaly_detection_flags_outliers(sample_feed, tmp_path):
    baseline = pd.DataFrame(
        [
            {
                "state": "CO",
                "industry": "Manufacturing",
                "jobs_created": 100,
                "investment_amount": 5.0,
            },
            {
                "state": "CO",
                "industry": "Manufacturing",
                "jobs_created": 120,
                "investment_amount": 6.0,
            },
        ]
    )
    anomaly_detector = AnomalyDetector(baseline)
    geocoder = StaticGeocoder({("boulder", "co"): (40.01499, -105.27055)})
    ingestor = ExpansionsIngestor(
        feeds=[sample_feed],
        geocoder=geocoder,
        anomaly_detector=anomaly_detector,
    )
    events = ingestor.scan()
    event = events[0]
    assert event.anomaly_flags
    assert any(flag.startswith("jobs_zscore") for flag in event.anomaly_flags)
    assert ingestor.review_queue.items


def test_metrics_track_processed_and_review_counts(sample_feed):
    entry = DummyEntry(
        title="Small business networking",
        summary="Networking event",
        link="https://example.com/meetup",
        published="2025-02-18T12:00:00",
        content=[{"value": "Entrepreneurs will gather in Denver."}],
        id="def-456",
    )

    def fake_parse(url):
        return DummyFeed([entry])

    import aker_core.expansions.ingestor as ingestor_module

    original_parse = ingestor_module.feedparser.parse
    ingestor_module.feedparser.parse = fake_parse
    try:
        feed = FeedConfig(url="https://example.com/rss", label="test_feed")
        ingestor = ExpansionsIngestor(feeds=[feed])
        ingestor.scan()
    finally:
        ingestor_module.feedparser.parse = original_parse

    assert ingestor.metrics.events_processed == 1
    assert ingestor.review_queue.items
