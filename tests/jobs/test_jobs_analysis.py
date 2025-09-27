from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from aker_jobs import (
    aggregate_migration_to_msa,
    awards_per_100k,
    awards_trend,
    business_formation_rate,
    business_survival_trend,
    cagr,
    classify_expansion,
    compute_trend,
    location_quotient,
    migration_net_25_44,
    summarise_expansions,
)


class TestLocationQuotient:
    def test_location_quotient_basic(self) -> None:
        df = pd.DataFrame(
            {
                "sector": ["tech", "health"],
                "local_jobs": [2000, 3000],
                "national_jobs": [100_000, 150_000],
                "population": [500_000, 500_000],
            }
        )

        result = location_quotient(df, population_column="population")
        assert pytest.approx(result.loc[result["sector"] == "tech", "lq"].iat[0], rel=1e-6) == (
            (2000 / 5000) / (100_000 / 250_000)
        )
        assert "jobs_per_100k" in result.columns

    def test_location_quotient_requires_population(self) -> None:
        df = pd.DataFrame({"sector": ["tech"], "local_jobs": [100], "national_jobs": [1_000]})
        with pytest.raises(ValueError):
            location_quotient(df)

    def test_location_quotient_validates_shares(self) -> None:
        df = pd.DataFrame(
            {
                "sector": ["tech", "health"],
                "local_jobs": [200, 300],
                "national_jobs": [0, 0],
                "population": [100_000, 100_000],
            }
        )
        with pytest.raises(ValueError):
            location_quotient(df, population_column="population")


class TestTimeSeries:
    def test_cagr_positive_growth(self) -> None:
        series = pd.Series([100, 121, 150], index=pd.period_range("2020", periods=3, freq="Y"))
        value = cagr(series)
        assert value > 0
        assert pytest.approx(value, rel=1e-6) == ((150 / 100) ** (1 / 2)) - 1

    def test_cagr_handles_zero(self) -> None:
        series = pd.Series([0, 50, 100])
        value = cagr(series, years=2)
        assert np.isfinite(value)


class TestMigration:
    def test_net_migration_per_1k(self) -> None:
        df = pd.DataFrame({"inflow": [1200], "outflow": [800], "population": [50_000]})
        result = migration_net_25_44(df)
        assert pytest.approx(result.iat[0], rel=1e-6) == (400 / 50_000) * 1000

    def test_aggregate_migration_to_msa(self) -> None:
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
        assert set(aggregated["msa_id"]) == {"31080", "26420"}
        la_row = aggregated.loc[aggregated["msa_id"] == "31080"].iloc[0]
        assert la_row["inflow"] == 250
        assert la_row["outflow"] == 210
        assert la_row["population"] == 22_000

    def test_aggregate_migration_missing_mapping_raises(self) -> None:
        migration_df = pd.DataFrame(
            {
                "state": ["06"],
                "county": ["001"],
                "inflow": [100],
                "outflow": [90],
                "population": [10_000],
            }
        )
        crosswalk = pd.DataFrame({"state": ["06"], "county": ["003"], "msa_id": ["12345"]})
        with pytest.raises(ValueError, match="Missing MSA mapping"):
            aggregate_migration_to_msa(migration_df, crosswalk)


class TestExpansions:
    def test_classify_and_summarise_expansions(self) -> None:
        raw = {
            "name": "New Chip Plant",
            "description": "Major semiconductor foundry",
            "jobs_created": 1500,
        }
        event = classify_expansion(raw)
        assert event.sector == "semiconductor"

        summary = summarise_expansions([event])
        assert summary["total_events"] == 1
        assert summary["jobs_semiconductor"] == 1500


class TestAwards:
    def test_awards_per_100k(self) -> None:
        df = pd.DataFrame(
            {
                "msa_id": ["123", "123"],
                "amount": [2_000_000, 3_000_000],
                "population": [500_000, 500_000],
            }
        )
        result = awards_per_100k(df, groupby_columns=["msa_id"])
        value = result.loc[result["msa_id"] == "123", "awards_per_100k"].iat[0]
        assert pytest.approx(value, rel=1e-6) == ((5_000_000 / 1_000_000) * 100_000)

    def test_awards_trend(self) -> None:
        df = pd.DataFrame(
            {
                "fiscal_year": [2021, 2022, 2023, 2024],
                "award_amount": [1_000_000, 1_200_000, 1_400_000, 1_680_000],
            }
        )
        trend = awards_trend(df, periods=1)
        assert len(trend) == 4
        # 2022 vs 2021 pct change
        assert pytest.approx(trend.loc[trend["period"] == "2022", "trend"].iat[0], rel=1e-6) == 0.2


class TestTrendUtilities:
    def test_compute_trend_generic(self) -> None:
        df = pd.DataFrame(
            {
                "period": pd.date_range("2023-01-01", periods=6, freq="M"),
                "value": [10, 12, 9, 15, 18, 21],
            }
        )
        result = compute_trend(df, date_column="period", value_column="value", freq="M", periods=1)
        assert result.shape[0] == 6
        assert (
            pytest.approx(result.loc[result["period"] == "2023-03", "trend"].iat[0], rel=1e-6)
            == (9 / 12) - 1
        )

    def test_business_survival_trend(self) -> None:
        df = pd.DataFrame(
            {
                "period": ["2020", "2021", "2022", "2023"],
                "survival_rate": [0.75, 0.78, 0.8, 0.82],
            }
        )
        result = business_survival_trend(df)
        assert "trend" in result.columns
        assert result.loc[result["period"] == "2021", "trend"].iat[0] == pytest.approx(
            (0.78 / 0.75) - 1, rel=1e-6
        )

    def test_compute_trend_invalid_dates(self) -> None:
        df = pd.DataFrame({"period": ["bad", "data"], "value": [1, 2]})
        with pytest.raises(ValueError):
            compute_trend(df, date_column="period", value_column="value")


class TestBusinessFormation:
    def test_business_formation_rate(self) -> None:
        df = pd.DataFrame(
            {
                "formations": [500],
                "population": [1_000_000],
                "existing": [50_000],
            }
        )
        metrics = business_formation_rate(
            df,
            formations_column="formations",
            population_column="population",
            existing_businesses_column="existing",
        )
        assert pytest.approx(metrics["formation_rate"], rel=1e-6) == (500 / 1_000_000) * 100_000
        assert not np.isnan(metrics["startup_density"])
