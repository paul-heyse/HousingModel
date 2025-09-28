from __future__ import annotations

import sys
import types

import numpy as np
import pandas as pd
import pytest

if "feedparser" not in sys.modules:
    sys.modules["feedparser"] = types.SimpleNamespace(parse=lambda *a, **k: {"entries": []})

from aker_jobs import (
    aggregate_migration_to_msa,
    awards_per_100k,
    awards_trend,
    bea_gdp_per_capita,
    build_location_quotients_from_bls,
    business_formation_rate,
    business_survival_trend,
    cagr,
    classify_expansion,
    compute_trend,
    ipeds_enrollment_per_100k,
    location_quotient,
    migration_net_25_44,
    patents_per_100k,
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

    def test_build_location_quotients_from_bls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_df = pd.DataFrame(
            {
                "series_id": ["LOCAL", "NAT"],
                "year": [2023, 2023],
                "period": ["M12", "M12"],
                "period_name": ["December", "December"],
                "value": [2000, 100_000],
                "footnotes": [[], []],
            }
        )

        monkeypatch.setattr("aker_jobs.sources.fetch_bls_employment", lambda *a, **k: fake_df)

        result = build_location_quotients_from_bls(
            {"tech": {"local": "LOCAL", "national": "NAT"}},
            start_year=2021,
            end_year=2023,
            population={"tech": 500_000},
        )
        assert pytest.approx(result.loc[0, "lq"], rel=1e-6) == (2000 / 2000) / (100_000 / 100_000)
        assert result.loc[0, "jobs_per_100k"] == pytest.approx(400.0, rel=1e-6)


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


def test_bea_gdp_per_capita(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_df = pd.DataFrame(
        {
            "GeoFips": ["12345"],
            "GeoName": ["Sample MSA"],
            "TimePeriod": ["2022"],
            "DataValue": ["1,234"],
        }
    )

    monkeypatch.setattr("aker_jobs.sources.fetch_bea_data", lambda *a, **k: fake_df)

    result = bea_gdp_per_capita(
        "12345",
        years=[2022],
        population={"12345": 1000.0},
        api_key="key",
    )
    assert result.loc[0, "gdp_per_capita"] == pytest.approx(1.234, rel=1e-6)


def test_ipeds_enrollment_per_100k() -> None:
    df = pd.DataFrame(
        {
            "location.city": ["Austin", "Austin"],
            "location.state": ["TX", "TX"],
            "latest.student.enrollment.all": [3000, 2000],
        }
    )
    population = {("Austin", "TX"): 1_000_000.0}
    result = ipeds_enrollment_per_100k(
        df, enrollment_field="latest.student.enrollment.all", population=population
    )
    assert result.loc[0, "per_100k"] == pytest.approx(500.0, rel=1e-6)


def test_patents_per_100k() -> None:
    df = pd.DataFrame(
        {
            "patent_number": ["1", "2", "3"],
            "assignees": ["A", "B", "A"],
            "msa": ["Denver", "Denver", "Austin"],
        }
    )
    population = {"Denver": 700_000.0, "Austin": 1_000_000.0}
    result = patents_per_100k(df, location_field="msa", population=population)
    denver = result.loc[result["msa"] == "Denver", "patents_per_100k"].iat[0]
    assert denver == pytest.approx((2 / 700_000.0) * 100_000.0, rel=1e-6)


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
