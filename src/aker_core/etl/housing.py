"""ETL helpers for housing market pricing datasets (Zillow, Redfin, Apartment List)."""

from __future__ import annotations

import gzip
import io
from typing import Optional

import pandas as pd
import requests

from aker_data.lake import DataLake

ZILLOW_ZORI_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "City_zori_uc_sfr_tier_0.33_0.67_sm_sa_month.csv"
)
REDFIN_MARKET_TRACKER_URL = (
    "https://redfin-public-data.s3-us-west-2.amazonaws.com/"
    "redfin_market_tracker/zip_code_market_tracker.tsv000.gz"
)
APARTMENT_LIST_URL = "https://static.apartmentlist.com/research/city_rent_estimates.csv"
DEFAULT_TIMEOUT = 60


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "aker-core-etl/1.0"
    return session


def _read_csv_response(response: requests.Response, *, compression: Optional[str] = None) -> pd.DataFrame:
    if compression == "gzip":
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as handle:
            return pd.read_csv(handle)
    if response.headers.get("Content-Type", "").startswith("application/gzip") or response.url.endswith(".gz"):
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as handle:
            return pd.read_csv(handle, sep="\t")
    if response.url.endswith(".tsv"):
        return pd.read_csv(io.StringIO(response.text), sep="\t")
    return pd.read_csv(io.StringIO(response.text))


def load_zillow_zori(
    *,
    url: str = ZILLOW_ZORI_URL,
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "zillow_zori",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    frame = _read_csv_response(response)
    if "RegionID" in frame.columns:
        frame.rename(columns={"RegionName": "region_name"}, inplace=True)
    if as_of:
        frame["as_of"] = as_of
    if lake is not None:
        lake.write(frame, dataset, as_of or "latest")
    return frame


def load_redfin_market_tracker(
    *,
    url: str = REDFIN_MARKET_TRACKER_URL,
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "redfin_market_tracker",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as handle:
        frame = pd.read_csv(handle, sep="\t")
    if as_of:
        frame["as_of"] = as_of
    if lake is not None:
        lake.write(frame, dataset, as_of or "latest")
    return frame


def load_apartment_list_rent(
    *,
    url: str = APARTMENT_LIST_URL,
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "apartment_list_rent",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    client = client or _default_session()
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    frame = _read_csv_response(response)
    if as_of:
        frame["as_of"] = as_of
    if lake is not None:
        lake.write(frame, dataset, as_of or "latest")
    return frame


__all__ = [
    "load_zillow_zori",
    "load_redfin_market_tracker",
    "load_apartment_list_rent",
]
