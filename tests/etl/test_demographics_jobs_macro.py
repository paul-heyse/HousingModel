from __future__ import annotations

import io
import zipfile
from pathlib import Path

import requests

from aker_core.etl.demographics import load_census_acs, load_census_bfs
from aker_core.etl.jobs import load_bls_qcew, load_bls_timeseries, load_lodes
from aker_core.etl.macro import load_bea_regional


class DummyResponse:
    def __init__(self, *, json_data=None, text: str | None = None, content: bytes | None = None, status_code: int = 200):
        self._json = json_data
        self.text = text or ""
        self.content = content or b""
        self.status_code = status_code

    def json(self):
        if self._json is None:
            raise ValueError("No JSON data configured")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class DummyClient:
    def __init__(self):
        self.responses = {}

    def add_get(self, url: str, response: DummyResponse):
        self.responses[("GET", url)] = response

    def add_post(self, url: str, response: DummyResponse):
        self.responses[("POST", url)] = response

    def get(self, url: str, **kwargs):
        return self.responses[("GET", url)]

    def post(self, url: str, json=None, **kwargs):
        return self.responses[("POST", url)]


def test_load_census_acs_parses_numeric():
    client = DummyClient()
    client.add_get(
        "https://api.census.gov/data/2024/acs/acs5",
        DummyResponse(json_data=[["NAME", "B01001_001E", "state"], ["Denver County", "715522", "08"]]),
    )
    df = load_census_acs(
        year=2024,
        variables=["B01001_001E"],
        geo="state",
        geo_id="08",
        client=client,
    )
    assert df.loc[0, "B01001_001E"] == 715522
    assert df.loc[0, "year"] == 2024


def test_load_census_bfs_returns_dataframe():
    client = DummyClient()
    client.add_get(
        "https://api.census.gov/data/timeseries/eits/bfs",
        DummyResponse(json_data=[["cell_value", "data_type_code", "time"], ["1200", "BFN", "2024-08"]]),
    )
    df = load_census_bfs(time_expr="from 2024-01 to 2024-08", client=client)
    assert df.loc[0, "cell_value"] == 1200
    assert "seasonally_adj" in df.columns


def test_load_bls_timeseries_parses_series():
    client = DummyClient()
    client.add_post(
        "https://api.bls.gov/publicAPI/v2/timeseries/data",
        DummyResponse(
            json_data={
                "Results": {
                    "series": [
                        {
                            "seriesID": "LAUS123",
                            "data": [
                                {"year": "2024", "period": "M08", "value": "3.5", "footnotes": []},
                            ],
                        }
                    ]
                }
            }
        ),
    )
    df = load_bls_timeseries(series_ids=["LAUS123"], start_year=2023, end_year=2024, client=client)
    assert df.loc[0, "value"] == 3.5


def test_load_bls_qcew_reads_csv():
    csv_text = "area_fips,own_code,industry_code,qtr,month1_emplvl\n08001,0,10,1,500"
    client = DummyClient()
    client.add_get(
        "https://data.bls.gov/cew/data/api/2024/1/area/08001.csv",
        DummyResponse(text=csv_text),
    )
    df = load_bls_qcew(area_code="08001", year=2024, quarter=1, client=client)
    assert df.loc[0, "month1_emplvl"] == 500


def test_load_lodes_reads_zipped_csv(tmp_path: Path):
    csv_bytes = io.BytesIO()
    with zipfile.ZipFile(csv_bytes, "w") as zf:
        zf.writestr("co_wac.csv", "w_geocode,emp\n08001000000,120\n")
    client = DummyClient()
    client.add_get(
        "https://lehd.ces.census.gov/data/lodes/LODES8/co/wac/co_wac_main.zip",
        DummyResponse(content=csv_bytes.getvalue()),
    )
    df = load_lodes(state="co", segment="wac", part="main", client=client)
    assert df.loc[0, "emp"] == 120


def test_load_bea_regional_extracts_values():
    client = DummyClient()
    client.add_get(
        "https://apps.bea.gov/api/data",
        DummyResponse(
            json_data={
                "BEAAPI": {
                    "Results": {
                        "Data": [
                            {"GeoName": "Denver", "TimePeriod": "2024", "DataValue": "12345"}
                        ]
                    }
                }
            }
        ),
    )
    df = load_bea_regional(
        dataset_name="Regional",
        table_name="CAINC1",
        geo_fips="MSA",
        year="2024",
        client=client,
    )
    assert df.loc[0, "DataValue"] == 12345
