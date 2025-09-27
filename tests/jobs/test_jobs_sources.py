from __future__ import annotations

import json
from typing import Any, Dict

import pytest
import requests

from aker_jobs import (
    DataIntegrationError,
    fetch_census_bfs,
    fetch_expansion_events,
    fetch_irs_migration,
    fetch_nih_reporter_projects,
    fetch_nsf_awards,
    fetch_usaspending_contracts,
)


class DummyResponse:
    def __init__(self, payload: Any, status: int = 200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self) -> Any:
        return self._payload


class DummySession:
    def __init__(self):
        self.requests: Dict[str, Dict[str, Any]] = {}

    def get(self, url: str, params: Dict[str, Any] | None = None, timeout: int = 0):
        self.requests[url] = {"params": params, "timeout": timeout}
        return DummyResponse(
            [
                ["time", "sector", "NAICS2017", "BFN", "state"],
                ["2023", "11", "00", "100", "06"],
            ]
        )

    def post(self, url: str, headers: Dict[str, str], data: str, timeout: int = 0):
        self.requests[url] = {"headers": headers, "data": data, "timeout": timeout}
        if "reporter.nih" in url:
            payload = {"results": [{"project_num": "1", "award_amount": 1000}]}
        elif "usaspending" in url:
            payload = {"results": [{"award_id": 1, "obligation": 12345}]}
        else:
            payload = {}
        return DummyResponse(payload)


def test_fetch_census_bfs_builds_expected_query() -> None:
    session = DummySession()
    df = fetch_census_bfs(state="06", start=2020, end=2023, session=session)
    assert df.shape[0] == 1
    request_args = session.requests["https://api.census.gov/data/timeseries/bfs/BFS"]
    assert request_args["params"]["for"] == "state:06"


def test_fetch_irs_migration_returns_dataframe(monkeypatch) -> None:
    session = DummySession()

    def fake_get(url: str, params: Dict[str, Any] | None = None, timeout: int = 0):
        session.requests[url] = {"params": params, "timeout": timeout}
        return DummyResponse(
            [
                ["State", "County", "AGI_CLASS", "N1", "N2"],
                ["06", "001", "1", "100", "120"],
            ]
        )

    session.get = fake_get  # type: ignore
    df = fetch_irs_migration(year=2022, state="06", session=session)
    assert df["N1"].iat[0] == 100
    request_args = session.requests["https://api.census.gov/data/timeseries/irs/migration"]
    assert request_args["params"]["time"] == 2022


def test_fetch_nih_reporter_projects(monkeypatch) -> None:
    session = DummySession()
    df = fetch_nih_reporter_projects(fiscal_years=[2022], org_names=["MIT"], session=session)
    assert df["award_amount"].iat[0] == 1000
    (nih_url,) = [url for url in session.requests if "reporter.nih" in url]
    payload = json.loads(session.requests[nih_url]["data"])
    assert payload["criteria"]["fy"] == [2022]


def test_fetch_nsf_awards(monkeypatch) -> None:
    session = DummySession()

    def fake_get(url: str, params: Dict[str, Any] | None = None, timeout: int = 0):
        session.requests[url] = {"params": params, "timeout": timeout}
        payload = {"response": {"award": [{"id": 1, "fundsObligatedAmt": "5000"}]}}
        return DummyResponse(payload)

    session.get = fake_get  # type: ignore
    df = fetch_nsf_awards(program="ENG", session=session)
    assert df["fundsObligatedAmt"].iat[0] == 5000


def test_fetch_usaspending_contracts(monkeypatch) -> None:
    session = DummySession()
    df = fetch_usaspending_contracts(keywords=["defense"], fiscal_year=2023, session=session)
    assert df["obligation"].iat[0] == 12345
    (spending_url,) = [url for url in session.requests if "usaspending" in url]
    payload = json.loads(session.requests[spending_url]["data"])
    assert payload["filters"]["keywords"] == ["defense"]


def test_census_error(monkeypatch) -> None:
    class ErrorSession:
        def get(self, *args: Any, **kwargs: Any):
            return DummyResponse({}, status=500)

    with pytest.raises(DataIntegrationError):
        fetch_census_bfs(state="06", start=2020, end=2021, session=ErrorSession())


def test_fetch_expansion_events(monkeypatch) -> None:
    from aker_jobs.metrics import ExpansionEvent as JobsExpansionEvent

    class DummyIngestor:
        def __init__(self, *_, **__):
            self.feeds = __.get("feeds")

        def scan(self):
            return [
                JobsExpansionEvent(
                    name="TechCorp",
                    sector="technology",
                    announcement_date=None,
                    jobs_created=200,
                    investment_musd=120.0,
                )
            ]

    events = fetch_expansion_events(["https://example.com/feed"], ingestor_factory=DummyIngestor)
    event = events[0]
    name = getattr(event, "company", getattr(event, "name", None))
    assert name == "TechCorp"
