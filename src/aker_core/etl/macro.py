"""ETL helpers for macroeconomic data feeds (BEA)."""

from __future__ import annotations

from typing import Optional

import pandas as pd
import requests

from aker_data.lake import DataLake

BEA_REGIONAL_URL = "https://apps.bea.gov/api/data"
DEFAULT_TIMEOUT = 60


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "aker-core-etl/1.0"
    return session


def load_bea_regional(
    *,
    dataset_name: str,
    table_name: str,
    geo_fips: str = "MSA",
    year: str = "ALL",
    api_key: Optional[str] = None,
    client: Optional[requests.Session] = None,
    base_url: str = BEA_REGIONAL_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "bea_regional",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    params = {
        "method": "GetData",
        "DataSetName": dataset_name,
        "TableName": table_name,
        "GeoFIPS": geo_fips,
        "Year": year,
        "ResultFormat": "JSON",
    }
    if api_key:
        params["UserID"] = api_key

    response = client.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    data = payload.get("BEAAPI", {}).get("Results", {}).get("Data", [])
    frame = pd.DataFrame(data)

    numeric_cols = [col for col in frame.columns if col.endswith("_VALUE")] + ["DataValue"]
    for column in numeric_cols:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["dataset_name"] = dataset_name
    frame["table_name"] = table_name
    frame["geo_fips"] = geo_fips
    frame["as_of"] = as_of or frame.get("TimePeriod", pd.Series(["latest"])).iloc[0]

    if lake is not None and not frame.empty:
        lake.write(frame, dataset, frame["as_of"].iloc[0])

    return frame


__all__ = ["load_bea_regional"]
