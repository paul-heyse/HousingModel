"""Prefect flow for refreshing housing market pricing datasets."""

from __future__ import annotations

import time
from datetime import datetime

import pandas as pd

from aker_core.etl.housing import (
    load_apartment_list_rent,
    load_redfin_market_tracker,
    load_zillow_zori,
)
from aker_data.lake import DataLake

from .base import ETLFlow, etl_task, timed_flow, with_run_context


class HousingMarketFlow(ETLFlow):
    def __init__(self) -> None:
        super().__init__(
            "refresh_housing_market",
            "Refresh Zillow, Redfin, and Apartment List housing market datasets.",
        )

    @etl_task("load_zillow", "Load Zillow ZORI rent index")
    def load_zillow(self, as_of: str) -> pd.DataFrame:
        return load_zillow_zori(as_of=as_of)

    @etl_task("load_redfin", "Load Redfin market tracker")
    def load_redfin(self, as_of: str) -> pd.DataFrame:
        return load_redfin_market_tracker(as_of=as_of)

    @etl_task("load_apartment_list", "Load Apartment List rent estimates")
    def load_apartment_list(self, as_of: str) -> pd.DataFrame:
        return load_apartment_list_rent(as_of=as_of)

    @etl_task("store_housing_dataset", "Persist housing dataset to data lake")
    def store(self, df: pd.DataFrame, dataset: str, as_of: str) -> str:
        lake = DataLake()
        return lake.write(df, dataset, as_of)


@timed_flow
@with_run_context
def refresh_housing_market(as_of: str | None = None) -> dict[str, int]:
    flow = HousingMarketFlow()
    as_of_value = as_of or datetime.now().strftime("%Y-%m")
    flow.log_start(as_of=as_of_value)
    started = time.time()

    zillow_df = flow.load_zillow(as_of=as_of_value)
    redfin_df = flow.load_redfin(as_of=as_of_value)
    apt_df = flow.load_apartment_list(as_of=as_of_value)

    flow.store(zillow_df, dataset="zillow_zori", as_of=as_of_value)
    flow.store(redfin_df, dataset="redfin_market_tracker", as_of=as_of_value)
    flow.store(apt_df, dataset="apartment_list_rent", as_of=as_of_value)

    duration = time.time() - started
    flow.log_complete(
        duration,
        as_of=as_of_value,
        zillow_rows=len(zillow_df),
        redfin_rows=len(redfin_df),
        apartment_rows=len(apt_df),
    )
    return {
        "as_of": as_of_value,
        "zillow_rows": len(zillow_df),
        "redfin_rows": len(redfin_df),
        "apartment_rows": len(apt_df),
    }


__all__ = ["HousingMarketFlow", "refresh_housing_market"]
