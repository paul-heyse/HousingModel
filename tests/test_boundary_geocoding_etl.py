"""Unit tests for boundary and geocoding ETL helpers."""

from __future__ import annotations

import io
import zipfile
from typing import Any, Dict, List

import pandas as pd
import pytest
import requests

from aker_core.etl.boundaries import (
    TIGERWEB_LAYERS,
    load_openaddresses,
    load_tigerweb_layer,
)
from aker_core.etl.geocoding import CensusGeocoder, GeocodeResult


class FakeResponse:
    def __init__(self, *, json_data: Dict[str, Any] | None = None, content: bytes = b"") -> None:
        self._json = json_data or {}
        self.content = content

    def json(self) -> Dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:  # pragma: no cover - included for API parity
        return None


class FakeCache:
    def __init__(self, response_map: Dict[str, FakeResponse]) -> None:
        self._responses = response_map
        self.session = type("Session", (), {"request": self._request})()

    def fetch(self, url: str, *_, **__) -> FakeResponse:
        return self._responses[url]

    def _request(self, method: str, url: str, **__) -> FakeResponse:
        key = url if method.upper() == "GET" else f"{method}:{url}"
        return self._responses[key]


class FakeLake:
    def __init__(self) -> None:
        self.writes: List[Dict[str, Any]] = []

    def write(self, df: pd.DataFrame, dataset: str, as_of: str, **kwargs: Any) -> str:
        self.writes.append({"dataset": dataset, "as_of": as_of, "rows": len(df)})
        return f"/lake/{dataset}/as_of={as_of}"


def _build_tigerweb_payload() -> Dict[str, Any]:
    geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [-124.409591, 32.534156],
                [-114.131211, 32.534156],
                [-114.131211, 42.009518],
                [-124.409591, 42.009518],
                [-124.409591, 32.534156],
            ]
        ],
    }
    return {
        "features": [
            {
                "attributes": {"GEOID": "06", "NAME": "California", "STUSPS": "CA"},
                "geometry": geometry,
            }
        ]
    }


def _build_openaddresses_zip() -> bytes:
    data = pd.DataFrame(
        [
            {"lon": -105.2705, "lat": 40.015, "hash": "abc123", "number": "123", "street": "Main"},
            {"lon": -105.2705, "lat": 40.015, "hash": "abc123", "number": "123", "street": "Main"},
        ]
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        with zf.open("addresses.csv", "w") as handle:
            handle.write(data.to_csv(index=False).encode("utf-8"))
    return buffer.getvalue()


def test_load_tigerweb_layer_normalises_geometry() -> None:
    payload = _build_tigerweb_payload()
    config = TIGERWEB_LAYERS["states"]
    request = requests.Request(
        method="GET",
        url=f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/{config.service_path}/MapServer/{config.layer}/query",
        params={"where": "1=1", "outFields": "*", "f": "json"},
    )
    prepared = request.prepare()
    fake_cache = FakeCache({prepared.url: FakeResponse(json_data=payload)})

    gdf = load_tigerweb_layer(config=config, cache=fake_cache, lake=FakeLake(), as_of="2025-01")

    assert len(gdf) == 1
    assert gdf.crs is not None and gdf.crs.to_string() == "EPSG:4326"
    assert gdf.iloc[0]["STUSPS"] == "CA"
    assert gdf.iloc[0]["layer_name"] == "states"


def test_load_openaddresses_deduplicates_and_sets_geometry() -> None:
    content = _build_openaddresses_zip()
    fake_cache = FakeCache({
        "https://data.openaddresses.io/runs/2025-01/us-co-denver.zip": FakeResponse(content=content)
    })

    gdf = load_openaddresses(
        run_id="2025-01",
        dataset="us-co-denver",
        cache=fake_cache,
        lake=FakeLake(),
        as_of="2025-01",
    )

    assert len(gdf) == 1
    assert gdf.geometry.iloc[0] is not None
    assert gdf.geometry.iloc[0].x == pytest.approx(-105.2705)
    assert gdf.geometry.iloc[0].y == pytest.approx(40.015)


def test_census_geocoder_forward_formats_result_and_writes_to_lake() -> None:
    payload = {
        "result": {
            "addressMatches": [
                {
                    "matchedAddress": "123 MAIN ST",
                    "coordinates": {"x": -105.2705, "y": 40.015},
                    "tigerLine": {"side": "L"},
                }
            ]
        }
    }

    geocode_request = requests.Request(
        method="GET",
        url="https://geocoding.geo.census.gov/geocoder/locations/onelineaddress",
        params={"address": "123 Main St", "benchmark": "Public_AR_Current", "format": "json"},
    ).prepare()
    fake_cache = FakeCache({geocode_request.url: FakeResponse(json_data=payload)})

    geocoder = CensusGeocoder(cache=fake_cache)
    fake_lake = FakeLake()
    result = geocoder.forward("123 Main St", lake=fake_lake)

    assert isinstance(result, GeocodeResult)
    assert result.latitude == pytest.approx(40.015)
    assert result.longitude == pytest.approx(-105.2705)
    assert result.provider == "census"
    assert fake_lake.writes, "expected geocode result to be written to DataLake"
