from __future__ import annotations

import gzip
import io

import requests

from aker_core.etl.housing import (
    APARTMENT_LIST_URL,
    REDFIN_MARKET_TRACKER_URL,
    ZILLOW_ZORI_URL,
    load_apartment_list_rent,
    load_redfin_market_tracker,
    load_zillow_zori,
)


class DummyResponse:
    def __init__(self, *, text: str | None = None, content: bytes | None = None, status_code: int = 200, url: str = ""):
        self.text = text or ""
        self.content = content or b""
        self.status_code = status_code
        self.url = url
        self.headers: dict[str, str] = {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class DummyClient:
    def __init__(self) -> None:
        self.responses: dict[str, DummyResponse] = {}

    def add_get(self, url: str, response: DummyResponse) -> None:
        self.responses[url] = response

    def get(self, url: str, **kwargs) -> DummyResponse:
        return self.responses[url]


def test_load_zillow_zori_reads_csv() -> None:
    csv = "RegionID,RegionName,2024-01\n123,Denver,2000"
    client = DummyClient()
    client.add_get(
        "https://files.zillowstatic.com/research/public_csvs/zori/City_zori_uc_sfr_tier_0.33_0.67_sm_sa_month.csv",
        DummyResponse(text=csv, url=ZILLOW_ZORI_URL),
    )
    df = load_zillow_zori(client=client)
    assert list(df.columns)[:2] == ["RegionID", "region_name"]
    assert df.loc[0, "RegionID"] == 123


def test_load_redfin_market_tracker_handles_gzip() -> None:
    tsv = "region_id\tregion_type\tmedian_sale_price\n123\tcity\t450000"
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as gz:
        gz.write(tsv.encode("utf-8"))
    client = DummyClient()
    client.add_get(
        "https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/zip_code_market_tracker.tsv000.gz",
        DummyResponse(content=buffer.getvalue(), url=REDFIN_MARKET_TRACKER_URL),
    )
    df = load_redfin_market_tracker(client=client)
    assert df.loc[0, "median_sale_price"] == 450000


def test_load_apartment_list_rent_reads_csv() -> None:
    csv = "region_name,bedroom_type,2024-02\nDenver,1BR,1700"
    client = DummyClient()
    client.add_get(
        "https://static.apartmentlist.com/research/city_rent_estimates.csv",
        DummyResponse(text=csv, url=APARTMENT_LIST_URL),
    )
    df = load_apartment_list_rent(client=client)
    assert df.loc[0, "2024-02"] == 1700
