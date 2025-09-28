"""ETL helpers for labor market data feeds (BLS, QCEW, LODES)."""

from __future__ import annotations

import io
import zipfile
from typing import Optional, Sequence

import pandas as pd
import requests

from aker_data.lake import DataLake

BLS_TIMESERIES_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data"
BLS_QCEW_URL = "https://data.bls.gov/cew/data/api/{year}/{quarter}/area/{area_code}.csv"
LODES_BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/{state}/{segment}/{state}_{segment}_{part}.zip"

DEFAULT_TIMEOUT = 60


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "aker-core-etl/1.0"
    return session


def load_bls_timeseries(
    *,
    series_ids: Sequence[str],
    start_year: int,
    end_year: int,
    client: Optional[requests.Session] = None,
    base_url: str = BLS_TIMESERIES_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "bls_timeseries",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    if not series_ids:
        raise ValueError("series_ids must not be empty")

    client = client or _default_session()
    payload = {
        "seriesid": list(series_ids),
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    response = client.post(base_url, json=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    rows = []
    for series in data.get("Results", {}).get("series", []):
        sid = series.get("seriesID")
        for entry in series.get("data", []):
            rows.append(
                {
                    "series_id": sid,
                    "year": int(entry["year"]),
                    "period": entry["period"],
                    "value": float(entry["value"]),
                    "footnotes": entry.get("footnotes", []),
                }
            )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["as_of"] = as_of or f"{end_year}-12"

    if lake is not None and not frame.empty:
        lake.write(frame, dataset, frame["as_of"].iloc[0])

    return frame


def load_bls_qcew(
    *,
    area_code: str,
    year: int,
    quarter: int,
    client: Optional[requests.Session] = None,
    base_url: str = BLS_QCEW_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "bls_qcew",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    url = base_url.format(year=year, quarter=quarter, area_code=area_code)
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    frame = pd.read_csv(io.StringIO(response.text))
    frame["year"] = year
    frame["quarter"] = quarter
    frame["area_code"] = area_code
    frame["as_of"] = as_of or f"{year}-Q{quarter}"

    if lake is not None:
        lake.write(frame, dataset, frame["as_of"].iloc[0])

    return frame


def load_lodes(
    *,
    state: str,
    segment: str,
    part: str,
    client: Optional[requests.Session] = None,
    base_url: str = LODES_BASE_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "lodes",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    url = base_url.format(state=state, segment=segment, part=part)
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        csv_name = next(name for name in zf.namelist() if name.endswith(".csv"))
        with zf.open(csv_name) as handle:
            frame = pd.read_csv(handle)

    frame["state"] = state
    frame["segment"] = segment
    frame["part"] = part
    frame["as_of"] = as_of or frame.columns[-1] if not frame.empty else as_of

    if lake is not None:
        lake.write(frame, dataset, frame["as_of"].iloc[0] if "as_of" in frame else as_of or "latest")

    return frame


__all__ = ["load_bls_timeseries", "load_bls_qcew", "load_lodes"]
