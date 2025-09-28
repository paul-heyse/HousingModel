"""Market data refresh flow - ingests and transforms external market data."""

from __future__ import annotations

import pandas as pd

from aker_core.cache import fetch
from aker_core.validation import validate_data_quality
from aker_data.lake import DataLake

from .base import ETLFlow, etl_task, timed_flow, with_run_context


class MarketDataRefreshFlow(ETLFlow):
    """Flow for refreshing market data from external sources."""

    def __init__(self):
        super().__init__("refresh_market_data", "Refresh market data from external sources")

    @etl_task("ingest_census_data", "Ingest census income data from API")
    def ingest_census_data(self, year: str) -> dict:
        """Ingest census income data."""
        self.logger.info(f"Fetching census data for year {year}")

        # Use cache to fetch census data
        url = f"https://api.census.gov/data/{year}/acs/acs5"
        params = {
            "get": "NAME,B19013_001E,B01003_001E",
            "for": "metropolitan statistical area/micropolitan statistical area:*",
            "key": "YOUR_CENSUS_API_KEY",  # This should come from settings
        }

        response = fetch(url, params=params, ttl="7d")  # Cache for 7 days

        if response.status_code != 200:
            raise ValueError(f"Census API returned {response.status_code}: {response.text}")

        data = response.json()
        self.logger.info(f"Retrieved {len(data)} records from census API")

        return {
            "year": year,
            "data": data[1:],  # Skip header row
            "headers": data[0],
            "source": "census_api",
        }

    @etl_task("transform_census_data", "Transform raw census data into DataFrame")
    def transform_census_data(self, census_data: dict) -> pd.DataFrame:
        """Transform census data into structured DataFrame."""
        headers = census_data["headers"]
        data = census_data["data"]

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Clean column names
        df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace(",", "")

        # Convert data types
        df["b19013_001e"] = pd.to_numeric(df["b19013_001e"], errors="coerce")  # Median income
        df["b01003_001e"] = pd.to_numeric(df["b01003_001e"], errors="coerce")  # Population

        # Add metadata columns
        df["data_year"] = census_data["year"]
        df["source"] = census_data["source"]
        df["ingested_at"] = pd.Timestamp.now()

        # Filter out invalid records
        df = df.dropna(subset=["b19013_001e", "b01003_001e"])

        self.logger.info(f"Transformed {len(df)} valid records")
        return df

    @etl_task("store_market_data", "Store processed market data in data lake")
    def store_market_data(self, df: pd.DataFrame, as_of: str) -> str:
        """Store market data in data lake."""
        lake = DataLake()

        # Store in data lake with partitioning
        result_path = lake.write(
            df, dataset="census_income", as_of=as_of, partition_by=["data_year"]
        )

        self.logger.info(f"Stored market data to {result_path}")
        return result_path

    @etl_task("validate_data_quality", "Validate data quality and completeness")
    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """Validate data quality using the unified schema stack."""
        validation_result = validate_data_quality(
            df=df,
            dataset_type="acs",
            fail_on_error=True,
        )

        self.logger.info(
            f"Data validation passed: {validation_result['successful_expectations']}/{validation_result['total_expectations']} checks"
        )
        return True


@timed_flow
@with_run_context
def refresh_market_data(year: str = "2022", as_of: str = None) -> str:
    """Refresh market data from external sources.

    Args:
        year: Census data year to fetch
        as_of: As-of date for partitioning (YYYY-MM format)

    Returns:
        Path to stored data
    """
    if as_of is None:
        from datetime import datetime

        as_of = datetime.now().strftime("%Y-%m")

    flow = MarketDataRefreshFlow()

    # Log flow start
    flow.log_start(year=year, as_of=as_of)

    try:
        # Execute ETL pipeline
        census_data = flow.ingest_census_data(year)
        df = flow.transform_census_data(census_data)
        flow.validate_data_quality(df)
        result_path = flow.store_market_data(df, as_of)

        flow.log_complete(0.0, records_processed=len(df), year=year, as_of=as_of)
        return result_path

    except Exception as e:
        flow.log_error(str(e), 0.0, year=year, as_of=as_of)
        raise


if __name__ == "__main__":
    # For local testing
    import sys

    if len(sys.argv) > 1:
        year = sys.argv[1]
    else:
        year = "2022"

    if len(sys.argv) > 2:
        as_of = sys.argv[2]
    else:
        as_of = None

    result = refresh_market_data(year=year, as_of=as_of)
    print(f"Market data refresh completed: {result}")
