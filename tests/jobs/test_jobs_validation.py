from __future__ import annotations

import math
from time import perf_counter

import numpy as np
import pandas as pd
import pytest

from aker_jobs import (
    aggregate_migration_to_msa,
    awards_trend,
    business_formation_rate,
    business_survival_trend,
    compute_trend,
    location_quotient,
    migration_net_25_44,
)


def test_location_quotient_benchmark() -> None:
    df = pd.DataFrame(
        {
            "sector": ["tech", "health"],
            "local_jobs": [5000, 3000],
            "national_jobs": [200_000, 120_000],
            "population": [1_000_000, 1_000_000],
        }
    )
    result = location_quotient(df, population_column="population")
    expected_tech = (5000 / 8000) / (200_000 / 320_000)
    assert math.isclose(result.loc[result["sector"] == "tech", "lq"].iat[0], expected_tech)


def test_bfs_vs_manual_totals() -> None:
    bfs = pd.DataFrame(
        {
            "formations": [100, 150, 200],
            "population": [50_000, 75_000, 100_000],
            "existing": [5_000, 7_000, 9_000],
        }
    )
    metrics = business_formation_rate(
        bfs,
        formations_column="formations",
        population_column="population",
        existing_businesses_column="existing",
    )
    manual_rate = (100 + 150 + 200) / (50_000 + 75_000 + 100_000) * 100_000
    assert math.isclose(metrics["formation_rate"], manual_rate)


def test_crosswalk_cross_validation() -> None:
    migration_df = pd.DataFrame(
        {
            "state": ["06", "06", "48"],
            "county": ["001", "013", "201"],
            "inflow": [100, 150, 80],
            "outflow": [90, 120, 70],
            "population": [10_000, 12_000, 8_000],
        }
    )
    crosswalk = pd.DataFrame(
        {
            "state": ["06", "06", "48"],
            "county": ["001", "013", "201"],
            "msa_id": ["31080", "31080", "26420"],
        }
    )
    aggregated = aggregate_migration_to_msa(migration_df, crosswalk)

    county_total_net = (migration_df["inflow"] - migration_df["outflow"]).sum()
    county_total_population = migration_df["population"].sum()
    expected_per_1k = (county_total_net / county_total_population) * 1000

    msa_net_series = migration_net_25_44(aggregated)
    weighted_msa_per_1k = (
        (msa_net_series * aggregated["population"]).sum() / aggregated["population"].sum()
    )

    assert math.isclose(weighted_msa_per_1k, expected_per_1k)


def test_awards_trend_matches_manual() -> None:
    data = pd.DataFrame(
        {
            "fiscal_year": [2021, 2022, 2023],
            "award_amount": [1_000_000, 1_050_000, 1_200_000],
        }
    )
    trend = awards_trend(data, periods=1)
    pct_change = (1_050_000 / 1_000_000) - 1
    assert math.isclose(trend.loc[trend["period"] == "2022", "trend"].iat[0], pct_change)


@pytest.mark.slow
def test_compute_trend_performance() -> None:
    rows = 50_000
    df = pd.DataFrame(
        {
            "period": pd.date_range("2015-01-01", periods=rows, freq="D"),
            "value": np.random.rand(rows),
        }
    )
    start = perf_counter()
    compute_trend(df, date_column="period", value_column="value", freq="M", periods=1)
    duration = perf_counter() - start
    assert duration < 1.5  # seconds


def test_business_survival_trend_benchmark() -> None:
    df = pd.DataFrame(
        {
            "period": ["2020", "2021", "2022"],
            "survival_rate": [0.70, 0.72, 0.75],
        }
    )
    trend = business_survival_trend(df)
    assert "trend" in trend.columns
    assert math.isclose(trend.loc[trend["period"] == "2021", "trend"].iat[0], (0.72 / 0.70) - 1)


def test_end_to_end_market_jobs_pipeline() -> None:
    naics_counts = pd.DataFrame(
        {
            "sector": ["tech", "health"],
            "local_jobs": [6000, 4000],
            "national_jobs": [120_000, 100_000],
            "population": [900_000, 900_000],
        }
    )
    lq = location_quotient(naics_counts, population_column="population")

    migration_df = pd.DataFrame({"inflow": [2000], "outflow": [1500], "population": [80_000]})
    migration_metric = migration_net_25_44(migration_df).iat[0]

    awards_df = pd.DataFrame({"fiscal_year": [2022, 2023], "award_amount": [10_000, 12_000]})
    awards_growth = awards_trend(awards_df, periods=1).iloc[-1]["trend"]

    assert lq["lq"].notna().all()
    assert migration_metric > 0
    assert awards_growth > -1  # sanity check
