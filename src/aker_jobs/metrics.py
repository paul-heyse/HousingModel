"""Higher-level metrics for innovation and jobs analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExpansionEvent:
    """Structured representation of an economic expansion announcement."""

    name: str
    sector: str
    announcement_date: date | None = None
    jobs_created: int | None = None
    investment_musd: float | None = None
    expected_completion: date | None = None


_SECTOR_KEYWORDS: Mapping[str, Sequence[str]] = {
    "university": ("university", "college", "campus"),
    "health": ("hospital", "health", "clinic"),
    "semiconductor": ("foundry", "chip", "semiconductor"),
    "defense": ("defense", "aerospace", "air force", "navy"),
}


def location_quotient(
    naics_counts: pd.DataFrame,
    *,
    sector_column: str = "sector",
    local_jobs_column: str = "local_jobs",
    national_jobs_column: str = "national_jobs",
    population_column: str | None = None,
    per_100k: bool = True,
) -> pd.DataFrame:
    """Compute location quotient metrics for a NAICS breakdown.

    The input must contain one row per sector with local and national job counts. An
    optional population column enables per-100k normalisation.
    """

    required = {sector_column, local_jobs_column, national_jobs_column}
    missing = required.difference(naics_counts.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    df = naics_counts.copy()
    df = df.astype({local_jobs_column: float, national_jobs_column: float})

    local_total = float(df[local_jobs_column].sum())
    national_total = float(df[national_jobs_column].sum())
    if local_total <= 0 or national_total <= 0:
        raise ValueError("Job totals must be positive for LQ computation")

    df["local_share"] = df[local_jobs_column] / local_total
    df["national_share"] = df[national_jobs_column] / national_total
    df["lq"] = df["local_share"] / df["national_share"]

    if not np.isclose(df["national_share"].sum(), 1.0, atol=1e-6):
        raise ValueError("National shares must sum to 1.0")

    if per_100k:
        if population_column is None:
            raise ValueError("population_column is required when per_100k=True")
        if population_column not in df.columns:
            raise KeyError(f"Missing population column '{population_column}'")
        population = df[population_column].astype(float)
        if (population <= 0).any():
            raise ValueError("Population must be positive for per-100k normalisation")
        df["jobs_per_100k"] = (df[local_jobs_column] / population) * 100_000.0

    return df[[sector_column, "lq"] + (["jobs_per_100k"] if per_100k else [])]


def migration_net_25_44(
    migration_df: pd.DataFrame,
    *,
    inflow_column: str = "inflow",
    outflow_column: str = "outflow",
    population_column: str = "population",
    per_1k: bool = True,
) -> pd.Series:
    """Calculate net migration for the 25-44 demographic."""

    required = {inflow_column, outflow_column, population_column}
    missing = required.difference(migration_df.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    inflow = migration_df[inflow_column].astype(float)
    outflow = migration_df[outflow_column].astype(float)
    population = migration_df[population_column].astype(float)
    if (population <= 0).any():
        raise ValueError("Population must be positive")

    net = inflow - outflow
    result = net / population
    if per_1k:
        result *= 1_000.0
    return result.rename("net_migration_25_44")


def aggregate_migration_to_msa(
    migration_df: pd.DataFrame,
    crosswalk: pd.DataFrame,
    *,
    migration_state_column: str = "state",
    migration_county_column: str = "county",
    crosswalk_state_column: str = "state",
    crosswalk_county_column: str = "county",
    crosswalk_msa_column: str = "msa_id",
    value_columns: Sequence[str] | None = None,
    require_complete_mapping: bool = True,
) -> pd.DataFrame:
    """Aggregate county-level migration data to MSA geography.

    Parameters
    ----------
    migration_df:
        IRS/Census migration records containing state and county identifiers and
        the numeric columns to aggregate (e.g., ``inflow``, ``outflow``,
        ``population``).
    crosswalk:
        DataFrame mapping state+county FIPS combinations to the desired MSA
        identifier.
    value_columns:
        Optional explicit list of columns to aggregate. When omitted, all
        numeric columns in ``migration_df`` are summed.
    require_complete_mapping:
        When ``True`` (default), raises :class:`ValueError` if any migration rows
        are missing an MSA mapping in the crosswalk.

    Returns
    -------
    DataFrame
        Aggregated metrics keyed by ``msa_id``.
    """

    if (
        migration_state_column not in migration_df.columns
        or migration_county_column not in migration_df.columns
    ):
        raise KeyError("Migration data must include state and county columns")

    if (
        crosswalk_state_column not in crosswalk.columns
        or crosswalk_county_column not in crosswalk.columns
    ):
        raise KeyError("Crosswalk must include state and county columns")

    if crosswalk_msa_column not in crosswalk.columns:
        raise KeyError("Crosswalk must include an MSA identifier column")

    merged = migration_df.merge(
        crosswalk[[crosswalk_state_column, crosswalk_county_column, crosswalk_msa_column]],
        left_on=[migration_state_column, migration_county_column],
        right_on=[crosswalk_state_column, crosswalk_county_column],
        how="left",
        validate="many_to_one",
    )

    if require_complete_mapping and merged[crosswalk_msa_column].isna().any():
        missing = merged[merged[crosswalk_msa_column].isna()][
            [migration_state_column, migration_county_column]
        ].drop_duplicates()
        raise ValueError(
            "Missing MSA mapping for migration rows: "
            + ", ".join(
                f"{row[migration_state_column]}-{row[migration_county_column]}"
                for _, row in missing.iterrows()
            )
        )

    aggregated = merged.dropna(subset=[crosswalk_msa_column]).copy()

    if value_columns is None:
        value_columns = [
            col
            for col in aggregated.columns
            if pd.api.types.is_numeric_dtype(aggregated[col]) and col not in {crosswalk_msa_column}
        ]

    for column in value_columns:
        aggregated[column] = pd.to_numeric(aggregated[column], errors="coerce")

    grouped = aggregated.groupby(crosswalk_msa_column, dropna=False)[list(value_columns)].sum(
        min_count=1
    )
    return grouped.reset_index().rename(columns={crosswalk_msa_column: "msa_id"})


def classify_expansion(raw_event: Mapping[str, str | int | float | None]) -> ExpansionEvent:
    """Classify an expansion event into standardised sectors."""

    name = str(raw_event.get("name", "unknown")).strip()
    description = str(raw_event.get("description", "")).lower()
    explicit = str(raw_event.get("sector", "")).lower()

    sector = "other"
    search_text = f"{explicit} {description}".strip()
    for label, keywords in _SECTOR_KEYWORDS.items():
        if any(keyword in search_text for keyword in keywords):
            sector = label
            break

    jobs_created = raw_event.get("jobs_created")
    if jobs_created is not None:
        jobs_created = int(jobs_created)

    investment = raw_event.get("investment_musd")
    if investment is not None:
        investment = float(investment)

    return ExpansionEvent(
        name=name, sector=sector, jobs_created=jobs_created, investment_musd=investment
    )


def summarise_expansions(events: Iterable[ExpansionEvent]) -> pd.Series:
    """Summarise expansion events by sector and total job creation."""

    events_list = list(events)
    if not events_list:
        return pd.Series({"total_events": 0, "jobs_created": 0.0})

    df = pd.DataFrame(e.__dict__ for e in events_list)
    jobs = df["jobs_created"].fillna(0).astype(float)
    summary = {
        "total_events": float(len(events_list)),
        "jobs_created": float(jobs.sum()),
    }
    for sector, group in df.groupby("sector"):
        summary[f"events_{sector}"] = float(len(group))
        summary[f"jobs_{sector}"] = float(group["jobs_created"].fillna(0).sum())
    return pd.Series(summary)


def _latest_bls_value(series: pd.DataFrame, series_id: str) -> float:
    """Return the most recent value for a BLS series."""

    subset = series[series["series_id"] == series_id]
    if subset.empty:
        raise KeyError(f"Series '{series_id}' not present in BLS payload")

    def _period_key(row: pd.Series) -> tuple[int, int]:
        period = str(row.get("period", ""))
        month = 0
        if period.startswith("M") and len(period) == 3:
            month = int(period[1:])
        return (int(row.get("year", 0)), month)

    ordered = subset.assign(_sort=subset.apply(_period_key, axis=1)).sort_values("_sort", ascending=False)
    latest_row = ordered.iloc[0]
    value = latest_row.get("value")
    if pd.isna(value):
        raise ValueError(f"Latest value for series '{series_id}' is missing")
    return float(value)


def awards_per_100k(
    awards: pd.DataFrame,
    *,
    amount_column: str = "amount",
    population_column: str = "population",
    groupby_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Compute awards per 100k residents for NIH/NSF/DoD funding."""

    if amount_column not in awards.columns or population_column not in awards.columns:
        raise KeyError("Awards data must include amount and population columns")

    df = awards.copy()
    df[amount_column] = df[amount_column].astype(float)
    df[population_column] = df[population_column].astype(float)
    if (df[population_column] <= 0).any():
        raise ValueError("Population must be positive")

    group_cols = list(groupby_columns or [])
    grouped = df.groupby(group_cols, dropna=False)
    aggregated = grouped[[amount_column, population_column]].sum()
    aggregated["awards_per_100k"] = (
        aggregated[amount_column] / aggregated[population_column]
    ) * 100_000.0
    return aggregated.reset_index()


def build_location_quotients_from_bls(
    series_map: Mapping[str, Mapping[str, str]],
    *,
    start_year: int,
    end_year: int,
    population: Mapping[str, float] | float,
    api_key: str | None = None,
    session: Any | None = None,
) -> pd.DataFrame:
    """Fetch BLS employment data and compute sector-level location quotients."""

    from . import sources

    if not series_map:
        raise ValueError("series_map must include at least one sector")

    all_series: list[str] = []
    for config in series_map.values():
        try:
            all_series.extend([config["local"], config["national"]])
        except KeyError as exc:
            raise KeyError("Series config must include 'local' and 'national'") from exc

    bls_df = sources.fetch_bls_employment(
        all_series,
        start_year=start_year,
        end_year=end_year,
        api_key=api_key,
        session=session,
    )

    records: list[dict[str, float | str]] = []
    for sector, config in series_map.items():
        local_jobs = _latest_bls_value(bls_df, config["local"])
        national_jobs = _latest_bls_value(bls_df, config["national"])
        record: dict[str, float | str] = {
            "sector": sector,
            "local_jobs": local_jobs,
            "national_jobs": national_jobs,
        }
        if isinstance(population, Mapping):
            pop_value = population.get(sector)
            if pop_value is None:
                raise KeyError(f"Population missing for sector '{sector}'")
            record["population"] = float(pop_value)
        else:
            record["population"] = float(population)
        records.append(record)

    prepared = pd.DataFrame(records)
    return location_quotient(
        prepared,
        sector_column="sector",
        local_jobs_column="local_jobs",
        national_jobs_column="national_jobs",
        population_column="population",
    )


def business_formation_rate(
    bfs: pd.DataFrame,
    *,
    formations_column: str = "formations",
    population_column: str = "population",
    existing_businesses_column: str | None = None,
    per_100k: bool = True,
) -> pd.Series:
    """Calculate business formation metrics for a region."""

    required = {formations_column, population_column}
    missing = required.difference(bfs.columns)
    if missing:
        raise KeyError(f"Missing columns: {sorted(missing)}")

    formations = bfs[formations_column].astype(float)
    population = bfs[population_column].astype(float)
    if (population <= 0).any():
        raise ValueError("Population must be positive")

    rate = formations / population
    if per_100k:
        rate *= 100_000.0

    if existing_businesses_column and existing_businesses_column in bfs.columns:
        existing = bfs[existing_businesses_column].astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            density = np.where(existing > 0, formations / existing, np.nan)
    else:
        density = np.full_like(rate, np.nan)

    return pd.Series(
        {
            "formation_rate": float(rate.sum()),
            "startup_density": float(np.nanmean(density)),
        }
    )


def bea_gdp_per_capita(
    geo_fips: str,
    *,
    years: Sequence[int],
    population: Mapping[str, float],
    api_key: str,
    frequency: str = "A",
    session: Any | None = None,
) -> pd.DataFrame:
    """Compute GDP per capita using BEA regional economic accounts."""

    from . import sources

    raw = sources.fetch_bea_data(
        dataset="Regional",
        table_name="CAGDP9",
        geo_fips=geo_fips,
        years=years,
        frequency=frequency,
        api_key=api_key,
        session=session,
    )

    df = raw.copy()
    df["GeoFips"] = df["GeoFips"].str.strip()
    df["DataValue"] = pd.to_numeric(df["DataValue"].str.replace(",", ""), errors="coerce")
    df = df[df["DataValue"].notna()]
    df["population"] = df["GeoFips"].map(population).astype(float)
    if df["population"].isna().any():
        missing = df[df["population"].isna()]["GeoFips"].unique().tolist()
        raise KeyError(f"Population missing for BEA GeoFips: {missing}")
    df["gdp_per_capita"] = df["DataValue"] / df["population"]
    return df[["GeoFips", "GeoName", "TimePeriod", "DataValue", "population", "gdp_per_capita"]]


def _summarise_time_series(
    df: pd.DataFrame,
    *,
    date_column: str,
    value_column: str,
    freq: str,
) -> pd.Series:
    raw = df[date_column]
    if pd.api.types.is_numeric_dtype(raw):
        timestamps = pd.to_datetime(raw.astype(int).astype(str), format="%Y", errors="coerce")
    else:
        timestamps = pd.to_datetime(raw, errors="coerce")
        if timestamps.isna().all():
            timestamps = pd.to_datetime(raw.astype(str), format="%Y", errors="coerce")
    if timestamps.isna().all():
        raise ValueError("Unable to parse dates for trend computation")
    series = timestamps.dt.to_period(freq)
    if series.isna().all():
        raise ValueError("All date values are invalid; cannot compute trend")
    grouped = df.assign(_period=series).groupby("_period")[value_column].sum(min_count=1)
    grouped = grouped.sort_index()
    return grouped.astype(float)


def compute_trend(
    df: pd.DataFrame,
    *,
    date_column: str,
    value_column: str,
    freq: str = "Q",
    periods: int = 4,
) -> pd.DataFrame:
    """Compute period-over-period growth trends for a time series."""

    if value_column not in df.columns:
        raise KeyError(f"Missing value column '{value_column}'")

    series = _summarise_time_series(
        df, date_column=date_column, value_column=value_column, freq=freq
    )
    trend = series.pct_change(periods=periods)
    return pd.DataFrame(
        {
            "period": series.index.astype(str),
            value_column: series.values,
            "trend": trend.values,
        }
    )


def awards_trend(
    awards: pd.DataFrame,
    *,
    date_column: str = "fiscal_year",
    amount_column: str = "award_amount",
    freq: str = "Y",
    periods: int = 1,
) -> pd.DataFrame:
    """Calculate award funding trends over time."""

    return compute_trend(
        awards, date_column=date_column, value_column=amount_column, freq=freq, periods=periods
    )


def business_survival_trend(
    survival: pd.DataFrame,
    *,
    date_column: str = "period",
    survival_column: str = "survival_rate",
    freq: str = "Y",
    periods: int = 1,
) -> pd.DataFrame:
    """Analyse survival rate trends for new businesses."""

    return compute_trend(
        survival, date_column=date_column, value_column=survival_column, freq=freq, periods=periods
    )


def ipeds_enrollment_per_100k(
    ipeds_df: pd.DataFrame,
    *,
    enrollment_field: str,
    population: Mapping[tuple[str, str], float],
) -> pd.DataFrame:
    """Aggregate IPEDS enrollment by city/state and normalise per 100k residents."""

    if enrollment_field not in ipeds_df.columns:
        raise KeyError(f"Enrollment field '{enrollment_field}' not present")

    df = ipeds_df.copy()
    df[enrollment_field] = pd.to_numeric(df[enrollment_field], errors="coerce")
    df = df.dropna(subset=[enrollment_field])
    grouped = df.groupby(["location.city", "location.state"])[enrollment_field].sum()
    records: list[dict[str, float | str]] = []
    for (city, state), value in grouped.items():
        population_key = (city, state)
        pop = population.get(population_key)
        if pop is None:
            raise KeyError(f"Population missing for {population_key}")
        records.append(
            {
                "city": city,
                "state": state,
                enrollment_field: float(value),
                "per_100k": float(value) / float(pop) * 100_000.0,
            }
        )
    return pd.DataFrame(records)


def patents_per_100k(
    patents_df: pd.DataFrame,
    *,
    location_field: str,
    population: Mapping[str, float],
) -> pd.DataFrame:
    """Calculate patents per 100k residents for a PatentsView result set."""

    if location_field not in patents_df.columns:
        raise KeyError(f"Location field '{location_field}' not present in patents data")

    grouped = patents_df.groupby(location_field)["patent_number"].count()
    records: list[dict[str, float | str]] = []
    for location, count in grouped.items():
        pop = population.get(location)
        if pop is None:
            raise KeyError(f"Population missing for '{location}'")
        records.append(
            {
                location_field: location,
                "patent_count": float(count),
                "patents_per_100k": float(count) / float(pop) * 100_000.0,
            }
        )
    return pd.DataFrame(records)
