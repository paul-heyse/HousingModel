"""ETL helpers for supply and permit data sources."""

from __future__ import annotations

from typing import Any, Mapping, Optional

import pandas as pd
import requests

from aker_data.lake import DataLake

CENSUS_BPS_BASE_URL = "https://api.census.gov/data/timeseries/bps"
SOCRATA_BASE_URL = "https://{domain}/resource/{dataset_id}.json"
ARCGIS_QUERY_TEMPLATE = (
    "https://{host}/arcgis/rest/services/{service_path}/FeatureServer/{layer}/query"
    "?where={where}&outFields={out_fields}&f={fmt}"
)
DEFAULT_TIMEOUT = 60


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "aker-core-etl/1.0"
    return session


def load_census_bps(
    *,
    time_expr: str,
    geo: str,
    geo_id: str,
    api_key: Optional[str] = None,
    base_url: str = CENSUS_BPS_BASE_URL,
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "census_bps",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    """Load building permits timeseries from the Census BPS API."""

    client = client or _default_session()
    params = {
        "get": "month,year,permits",
        "time": time_expr,
        "geo": f"{geo}:{geo_id}",
    }
    if api_key:
        params["key"] = api_key

    response = client.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    header, rows = payload[0], payload[1:]
    frame = pd.DataFrame(rows, columns=header)
    frame["permits"] = pd.to_numeric(frame["permits"], errors="coerce")
    frame["month"] = pd.to_numeric(frame["month"], errors="coerce")
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["geo"] = geo
    frame["geo_id"] = geo_id
    frame["as_of"] = as_of or frame["year"].astype(str) + "-" + frame["month"].astype(str).str.zfill(2)

    if lake is not None:
        lake.write(frame, dataset, frame["as_of"].iloc[-1])

    return frame


def load_socrata_dataset(
    *,
    domain: str,
    dataset_id: str,
    app_token: Optional[str] = None,
    params: Optional[Mapping[str, Any]] = None,
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "socrata_dataset",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    """Load a dataset from a Socrata SODA endpoint."""

    client = client or _default_session()
    url = SOCRATA_BASE_URL.format(domain=domain, dataset_id=dataset_id)
    request_params = dict(params or {})
    headers: dict[str, str] = {}
    if app_token:
        headers["X-App-Token"] = app_token

    response = client.get(url, params=request_params, headers=headers, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    frame = pd.DataFrame(data)
    if as_of:
        frame["as_of"] = as_of
    if lake is not None:
        lake.write(frame, dataset, as_of or "latest")
    return frame


def load_arcgis_feature_layer(
    *,
    host: str,
    service_path: str,
    layer: int,
    where: str = "1=1",
    out_fields: str = "*",
    fmt: str = "json",
    client: Optional[requests.Session] = None,
    lake: Optional[DataLake] = None,
    dataset: str = "arcgis_feature_layer",
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    """Load features from an ArcGIS Feature Service layer."""

    client = client or _default_session()
    url = ARCGIS_QUERY_TEMPLATE.format(
        host=host,
        service_path=service_path,
        layer=layer,
        where=where,
        out_fields=out_fields,
        fmt=fmt,
    )
    response = client.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    features = payload.get("features", [])
    records = [
        {
            **(feature.get("attributes") or {}),
            "geometry": feature.get("geometry"),
        }
        for feature in features
    ]
    frame = pd.DataFrame(records)
    if as_of:
        frame["as_of"] = as_of
    if lake is not None:
        lake.write(frame, dataset, as_of or "latest")
    return frame


__all__ = [
    "load_census_bps",
    "load_socrata_dataset",
    "load_arcgis_feature_layer",
]
