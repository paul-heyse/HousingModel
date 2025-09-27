"""External data integrations for innovation and jobs analysis."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import pandas as pd
import requests

from aker_core.expansions import ExpansionEvent, ExpansionsIngestor, FeedConfig

_CENSUS_BASE = "https://api.census.gov/data"
_NIH_REPORTER_URL = "https://api.reporter.nih.gov/v2/projects/search"
_NSF_AWARDS_URL = "https://api.nsf.gov/services/v1/awards.json"
_USASPENDING_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
_BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
_BEA_API_URL = "https://apps.bea.gov/api/data/"
_IPEDS_API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
_PATENTSVIEW_API_URL = "https://api.patentsview.org/patents/query"


class DataIntegrationError(RuntimeError):
    """Raised when an external data integration fails."""


def _get_session(session: Optional[requests.Session]) -> requests.Session:
    return session or requests.Session()


def fetch_census_bfs(
    *,
    state: str,
    start: int,
    end: int,
    dataset: str = "bfs",
    measure: str = "BFN",
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch Census Business Formation Series metrics for a state.

    Parameters
    ----------
    state:
        Two-digit FIPS code for the state (e.g., ``06`` for California).
    start, end:
        Year range to query (inclusive).
    dataset:
        BFS dataset identifier. ``bfs`` corresponds to the Business Formation
        Statistics time series documented by the Census Bureau.
    measure:
        Measurement column requested. Examples include ``BFN`` (business
        formations) and ``HBA`` (high-propensity business applications).
    session:
        Optional pre-configured :class:`requests.Session` for testing or custom
        retry behaviour.
    """

    url = f"{_CENSUS_BASE}/timeseries/{dataset}/BFS"
    params = {
        "get": "time,sector,NAICS2017" + ("," + measure if measure else ""),
        "for": f"state:{state}",
        "time": f"{start}-{end}",
    }

    response = _get_session(session).get(url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network errors
        raise DataIntegrationError(f"Census BFS request failed: {exc}") from exc

    payload = response.json()
    if not payload:
        raise DataIntegrationError("Census BFS API returned no data")

    header, *rows = payload
    df = pd.DataFrame(rows, columns=header)
    numeric_cols = {measure, "time"}
    for col in numeric_cols.intersection(df.columns):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fetch_irs_migration(
    *,
    year: int,
    state: str,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch IRS migration flows for a given state and year."""

    url = f"{_CENSUS_BASE}/timeseries/irs/migration"
    params = {
        "get": "State,County,AGI_CLASS,N1,N2",
        "for": f"state:{state}",
        "time": year,
    }
    response = _get_session(session).get(url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover
        raise DataIntegrationError(f"IRS migration request failed: {exc}") from exc

    payload = response.json()
    if not payload:
        raise DataIntegrationError("IRS migration API returned no data")

    header, *rows = payload
    df = pd.DataFrame(rows, columns=header)
    for col in ("N1", "N2"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fetch_nih_reporter_projects(
    *,
    fiscal_years: Iterable[int],
    org_names: Optional[Iterable[str]] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch NIH RePORTER project grants for the specified fiscal years."""

    filters: Dict[str, Any] = {
        "fy": sorted(set(int(year) for year in fiscal_years)),
    }
    if org_names:
        filters["orgNames"] = list(org_names)

    payload = {
        "criteria": filters,
        "include_fields": [
            "project_num",
            "fiscal_year",
            "project_title",
            "award_amount",
            "org_name",
            "org_city",
            "org_state",
        ],
    }

    response = _get_session(session).post(
        _NIH_REPORTER_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover
        raise DataIntegrationError(f"NIH RePORTER request failed: {exc}") from exc

    payload = response.json()
    projects = payload.get("results") or []
    df = pd.DataFrame(projects)
    if not df.empty and "award_amount" in df.columns:
        df["award_amount"] = pd.to_numeric(df["award_amount"], errors="coerce")
    return df


def fetch_nsf_awards(
    *,
    program: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch NSF awards via the public awards service."""

    params: Dict[str, Any] = {}
    if program:
        params["program"] = program
    if start_date:
        params["dateStart"] = start_date
    if end_date:
        params["dateEnd"] = end_date

    response = _get_session(session).get(_NSF_AWARDS_URL, params=params, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover
        raise DataIntegrationError(f"NSF awards request failed: {exc}") from exc

    payload = response.json()
    awards = payload.get("response", {}).get("award", [])
    df = pd.DataFrame(awards)
    if not df.empty and "fundsObligatedAmt" in df.columns:
        df["fundsObligatedAmt"] = pd.to_numeric(df["fundsObligatedAmt"], errors="coerce")
    return df


def fetch_usaspending_contracts(
    *,
    keywords: Iterable[str],
    fiscal_year: int,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch contract awards from USAspending.gov for defence-related keywords."""

    filters = {
        "keywords": list(keywords),
        "time_period": [{"fiscal_year": fiscal_year, "date_type": "fiscal"}],
    }
    payload = {"filters": filters, "limit": 500, "page": 1}

    response = _get_session(session).post(
        _USASPENDING_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover
        raise DataIntegrationError(f"USAspending request failed: {exc}") from exc

    payload = response.json()
    results = payload.get("results") or []
    df = pd.DataFrame(results)
    return df


def fetch_expansion_events(
    feeds: Sequence[str],
    *,
    keywords: Optional[Sequence[str]] = None,
    confidence_threshold: float = 0.65,
    ingestor_factory: Callable[..., ExpansionsIngestor] | None = None,
) -> list[ExpansionEvent]:
    """Fetch expansion events from press-release feeds.

    Parameters
    ----------
    feeds:
        Sequence of RSS/Atom feed URLs to scan.
    keywords:
        Optional keyword filter passed through to the :class:`ExpansionsIngestor`.
    confidence_threshold:
        Minimum confidence score required for events to be returned.
    ingestor_factory:
        Optional factory to create a custom :class:`ExpansionsIngestor` instance
        (primarily for unit testing).
    """

    if not feeds:
        raise ValueError("At least one feed URL must be supplied")

    configs = [FeedConfig(url=url, label=f"feed_{idx}") for idx, url in enumerate(feeds, start=1)]

    factory = ingestor_factory or ExpansionsIngestor
    ingestor = factory(
        feeds=configs,
        keywords=keywords,
        confidence_threshold=confidence_threshold,
    )
    events = ingestor.scan()
    filtered: list[ExpansionEvent] = []
    for event in events:
        event_confidence = getattr(event, "confidence", confidence_threshold)
        if event_confidence is None or event_confidence >= confidence_threshold:
            filtered.append(event)
    return filtered


def fetch_bls_employment(
    series_ids: Sequence[str],
    *,
    start_year: int,
    end_year: int,
    api_key: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch employment data from the BLS public API.

    Parameters
    ----------
    series_ids:
        Sequence of BLS time-series identifiers (CES or QCEW).
    start_year, end_year:
        Inclusive year range to request.
    api_key:
        Optional BLS API key to unlock higher rate limits.
    session:
        Optional :class:`requests.Session` for custom retry configuration.
    """

    if not series_ids:
        raise ValueError("At least one BLS series id must be provided")

    payload: Dict[str, Any] = {
        "seriesid": list(series_ids),
        "startyear": int(start_year),
        "endyear": int(end_year),
    }
    if api_key:
        payload["registrationkey"] = api_key

    response = _get_session(session).post(_BLS_API_URL, json=payload, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network failure path
        raise DataIntegrationError(f"BLS API request failed: {exc}") from exc

    payload_json = response.json()
    results = payload_json.get("Results", {})
    series_list = results.get("series") or []
    if not series_list:
        raise DataIntegrationError("BLS API returned no series data")

    records: List[Dict[str, Any]] = []
    for series in series_list:
        series_id = series.get("seriesID")
        for entry in series.get("data", []):
            records.append(
                {
                    "series_id": series_id,
                    "year": int(entry.get("year", 0)),
                    "period": entry.get("period"),
                    "period_name": entry.get("periodName"),
                    "value": pd.to_numeric(entry.get("value"), errors="coerce"),
                    "footnotes": [note.get("text") for note in entry.get("footnotes", []) if note.get("text")],
                }
            )

    if not records:
        raise DataIntegrationError("BLS API response contained no data rows")

    return pd.DataFrame.from_records(records)


def fetch_bea_data(
    *,
    dataset: str,
    table_name: str,
    geo_fips: str,
    years: Sequence[int],
    api_key: str,
    frequency: str = "A",
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch data from the BEA API.

    Parameters
    ----------
    dataset:
        BEA dataset name (e.g., ``"Regional"``).
    table_name:
        Name of the BEA table (e.g., ``"CAGDP9"`` for GDP by metro area).
    geo_fips:
        Geography identifier or ``"MSA"`` wildcard.
    years:
        Iterable of years to request.
    api_key:
        BEA API key (required).
    frequency:
        Frequency code (``"A"`` annual, ``"Q"`` quarterly).
    session:
        Optional :class:`requests.Session`.
    """

    if not api_key:
        raise ValueError("A BEA API key is required")
    if not years:
        raise ValueError("At least one year must be specified for BEA data")

    params = {
        "UserID": api_key,
        "method": "GetData",
        "datasetname": dataset,
        "TableName": table_name,
        "GeoFips": geo_fips,
        "Year": ",".join(str(year) for year in sorted(set(years))),
        "Frequency": frequency,
        "ResultFormat": "JSON",
    }

    response = _get_session(session).get(_BEA_API_URL, params=params, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network failure path
        raise DataIntegrationError(f"BEA API request failed: {exc}") from exc

    payload_json = response.json()
    try:
        data_rows = payload_json["BEAAPI"]["Results"]["Data"]
    except KeyError as exc:  # pragma: no cover - unexpected structure
        raise DataIntegrationError("BEA API response missing data") from exc

    if not data_rows:
        raise DataIntegrationError("BEA API returned no data rows")

    return pd.DataFrame(data_rows)


def fetch_ipeds_enrollment(
    *,
    fields: Sequence[str],
    filters: Optional[Dict[str, Any]] = None,
    api_key: str,
    per_page: int = 100,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch higher-education enrollment data from the IPEDS/College Scorecard API."""

    if not api_key:
        raise ValueError("An API key is required for the IPEDS connector")
    if not fields:
        raise ValueError("At least one field must be requested from IPEDS")

    params: Dict[str, Any] = {
        "api_key": api_key,
        "per_page": per_page,
        "fields": ",".join(fields),
    }
    if filters:
        params.update(filters)

    response = _get_session(session).get(_IPEDS_API_URL, params=params, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network failure path
        raise DataIntegrationError(f"IPEDS API request failed: {exc}") from exc

    payload_json = response.json()
    results = payload_json.get("results") or []
    if not results:
        raise DataIntegrationError("IPEDS API returned no records")

    return pd.DataFrame(results)


def fetch_patentsview_innovations(
    *,
    location_filter: Dict[str, Any],
    fields: Sequence[str],
    per_page: int = 100,
    session: Optional[requests.Session] = None,
) -> pd.DataFrame:
    """Fetch patent data from the PatentsView API for innovation benchmarking."""

    if not fields:
        raise ValueError("PatentsView queries must request at least one field")

    payload = {
        "q": location_filter,
        "f": list(fields),
        "o": {"per_page": per_page},
    }

    response = _get_session(session).post(_PATENTSVIEW_API_URL, json=payload, timeout=60)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network failure path
        raise DataIntegrationError(f"PatentsView request failed: {exc}") from exc

    payload_json = response.json()
    patents = payload_json.get("patents") or []
    if not patents:
        raise DataIntegrationError("PatentsView returned no patents for the query")

    return pd.DataFrame(patents)
