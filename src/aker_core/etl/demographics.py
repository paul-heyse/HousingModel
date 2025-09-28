"""ETL helpers for demographic and business dynamism data feeds."""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import requests

from aker_data.lake import DataLake

CENSUS_ACS_BASE_URL = "https://api.census.gov/data/{year}/acs/acs5"
CENSUS_BFS_BASE_URL = "https://api.census.gov/data/timeseries/eits/bfs"

DEFAULT_TIMEOUT = 60


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "aker-core-etl/1.0"
    return session


def load_census_acs(
    *,
    year: int,
    variables: Sequence[str],
    geo: str,
    geo_id: str,
    api_key: Optional[str] = None,
    client: Optional[requests.Session] = None,
    base_url: str = CENSUS_ACS_BASE_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "acs_demographics",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    if not variables:
        raise ValueError("At least one ACS variable is required")

    client = client or _default_session()
    url = base_url.format(year=year)
    params = {
        "get": ",".join(variables),
        "for": f"{geo}:{geo_id}",
    }
    if api_key:
        params["key"] = api_key
    response = client.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    header, rows = payload[0], payload[1:]
    frame = pd.DataFrame(rows, columns=header)

    for var in variables:
        frame[var] = pd.to_numeric(frame[var], errors="coerce")
    frame["geo"] = geo
    frame["geo_id"] = geo_id
    frame["year"] = year
    frame["as_of"] = as_of or f"{year}-12"

    if lake is not None:
        lake.write(frame, dataset, frame["as_of"].iloc[0])

    return frame


def load_census_bfs(
    *,
    time_expr: str,
    seasonally_adjusted: str = "U",
    api_key: Optional[str] = None,
    client: Optional[requests.Session] = None,
    base_url: str = CENSUS_BFS_BASE_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "bfs_applications",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    params = {
        "get": "cell_value,data_type_code,time",
        "time": time_expr,
        "seasonally_adj": seasonally_adjusted,
    }
    if api_key:
        params["key"] = api_key
    response = client.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    header, rows = data[0], data[1:]
    frame = pd.DataFrame(rows, columns=header)
    frame["cell_value"] = pd.to_numeric(frame["cell_value"], errors="coerce")
    frame["seasonally_adj"] = seasonally_adjusted
    frame["as_of"] = as_of or frame["time"].iloc[-1]

    if lake is not None:
        lake.write(frame, dataset, frame["as_of"].iloc[0])

    return frame


__all__ = ["load_census_acs", "load_census_bfs"]
