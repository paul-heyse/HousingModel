from __future__ import annotations

import pytest
import requests

from aker_core.etl.supply import (
    load_arcgis_feature_layer,
    load_census_bps,
    load_socrata_dataset,
)


class DummyResponse:
    def __init__(self, *, json_data=None, status_code: int = 200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        if self._json is None:
            raise ValueError("No json data configured")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class DummyClient:
    def __init__(self):
        self.responses = {}

    def add_get(self, url, response):
        self.responses[("GET", url)] = response

    def get(self, url, **kwargs):
        return self.responses[("GET", url)]


def test_load_census_bps_coerces_numeric():
    client = DummyClient()
    client.add_get(
        "https://api.census.gov/data/timeseries/bps",
        DummyResponse(json_data=[["month", "year", "permits", "geo"], ["01", "2024", "120", "12345"]]),
    )
    df = load_census_bps(
        time_expr="from 2024-01 to 2024-03",
        geo="state",
        geo_id="08",
        client=client,
    )
    assert df.loc[0, "permits"] == 120
    assert df.loc[0, "geo_id"] == "08"


def test_load_socrata_dataset_parses_rows():
    client = DummyClient()
    client.add_get(
        "https://data.denvergov.org/resource/permits.json",
        DummyResponse(json_data=[{"permit": "ABC123", "status": "Open"}]),
    )
    df = load_socrata_dataset(
        domain="data.denvergov.org",
        dataset_id="permits",
        client=client,
    )
    assert df.loc[0, "permit"] == "ABC123"


def test_load_arcgis_feature_layer_extracts_attributes():
    client = DummyClient()
    payload = {
        "features": [
            {"attributes": {"permit_id": "1", "status": "Issued"}, "geometry": {"x": -105.0, "y": 39.0}}
        ]
    }
    client.add_get(
        "https://maps.example.com/arcgis/rest/services/Permits/FeatureServer/0/query?where=1=1&outFields=*&f=json",
        DummyResponse(json_data=payload),
    )
    df = load_arcgis_feature_layer(
        host="maps.example.com",
        service_path="Permits",
        layer=0,
        client=client,
    )
    assert df.loc[0, "permit_id"] == "1"
    assert df.loc[0, "status"] == "Issued"
    assert isinstance(df.loc[0, "geometry"], dict)


def test_dummy_response_raises_http_error() -> None:
    response = DummyResponse(status_code=500)
    with pytest.raises(requests.HTTPError):
        response.raise_for_status()
