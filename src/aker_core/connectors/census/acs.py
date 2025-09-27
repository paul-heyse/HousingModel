"""Census ACS (American Community Survey) data connector."""

from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd

from aker_core.cache import fetch

from ..base import DataConnector


class CensusACSConnector(DataConnector):
    """Connector for US Census Bureau American Community Survey (ACS) data."""

    def __init__(self, **kwargs):
        """Initialize Census ACS connector."""
        super().__init__(
            name="census_acs",
            base_url="https://api.census.gov/data",
            output_schema={
                "msa_id": "string",
                "msa_name": "string",
                "state": "string",
                "county": "string",
                "population": "int64",
                "median_household_income": "float64",
                "median_age": "float64",
                "bachelors_degree_pct": "float64",
                "unemployment_rate": "float64",
                "poverty_rate": "float64",
                "housing_units": "int64",
                "occupied_housing_units": "int64",
                "vacant_housing_units": "int64",
                "data_year": "int64",
                "collected_at": "datetime64[ns]",
            },
            **kwargs,
        )
        self.api_key = kwargs.get("api_key")

    def _fetch_raw_data(self, start_date: date, end_date: date, **kwargs) -> pd.DataFrame:
        """Fetch ACS data from Census API."""
        msa_ids = kwargs.get("msa_ids", [])
        tables = kwargs.get("tables", ["B19013_001E", "B01003_001E", "B15003_001E"])

        if not msa_ids:
            # Default to major MSAs if none specified
            msa_ids = [
                "31080",  # Los Angeles-Long Beach-Anaheim, CA
                "16980",  # Chicago-Naperville-Elgin, IL-IN-WI
                "19100",  # Dallas-Fort Worth-Arlington, TX
                "37980",  # Philadelphia-Camden-Wilmington, PA-NJ-DE-MD
                "26420",  # Houston-The Woodlands-Sugar Land, TX
                "47900",  # Washington-Arlington-Alexandria, DC-VA-MD-WV
                "33100",  # Miami-Fort Lauderdale-Pompano Beach, FL
                "12060",  # Atlanta-Sandy Springs-Alpharetta, GA
            ]

        all_data = []

        # Fetch data for each MSA
        for msa_id in msa_ids:
            try:
                msa_data = self._fetch_msa_data(msa_id, tables, start_date.year)
                if msa_data:
                    all_data.extend(msa_data)
            except Exception as e:
                self.logger.error(f"Failed to fetch data for MSA {msa_id}: {e}")

        if not all_data:
            raise ValueError("No data retrieved from Census API")

        return pd.DataFrame(all_data)

    def _fetch_msa_data(self, msa_id: str, tables: List[str], year: int) -> List[dict]:
        """Fetch ACS data for a specific MSA."""
        # Build query for multiple tables
        get_params = []
        for table in tables:
            if table == "B19013_001E":  # Median household income
                get_params.append("B19013_001E")
            elif table == "B01003_001E":  # Total population
                get_params.append("B01003_001E")
            elif table == "B15003_001E":  # Educational attainment
                get_params.append("B15003_001E")

        # Add geographic identifiers
        get_params.extend(["NAME", "state", "county"])

        endpoint = f"/{year}/acs/acs5"

        params = {
            "get": ",".join(get_params),
            "for": f"metropolitan statistical area/micropolitan statistical area:{msa_id}",
            "$limit": 50000,  # Reasonable limit
        }

        if self.api_key:
            params["key"] = self.api_key

        response = fetch(endpoint, params=params, ttl="30d")

        if response.status_code != 200:
            self.logger.error(f"Census API error for MSA {msa_id}: {response.status_code}")
            return []

        data = response.json()

        if len(data) <= 1:  # Header only or empty
            return []

        headers = data[0]
        rows = data[1:]

        msa_data = []
        for row in rows:
            record = dict(zip(headers, row))

            # Extract MSA name from NAME field (format: "MSA Name, State")
            msa_name = record.get("NAME", "")
            if ", " in msa_name:
                name_part, state_part = msa_name.rsplit(", ", 1)
                msa_name_clean = name_part
            else:
                msa_name_clean = msa_name

            msa_record = {
                "msa_id": msa_id,
                "msa_name": msa_name_clean,
                "state": record.get("state", ""),
                "county": record.get("county", ""),
                "population": self._parse_int(record.get("B01003_001E")),
                "median_household_income": self._parse_int(record.get("B19013_001E")),
                "data_year": year,
                "collected_at": pd.Timestamp.now(),
            }

            # Add additional fields if available
            if "B15003_001E" in record:
                # Calculate bachelor's degree percentage
                total_pop = self._parse_int(record.get("B15003_001E", "0"))
                bachelors_pop = self._parse_int(
                    record.get("B15003_022E", "0")
                )  # Bachelor's degree or higher
                if total_pop and total_pop > 0:
                    msa_record["bachelors_degree_pct"] = (bachelors_pop / total_pop) * 100

            msa_data.append(msa_record)

        return msa_data

    def _transform_to_dataframe(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Transform Census data to standardized format."""
        df = super()._transform_to_dataframe(raw_data)

        # Add calculated fields
        if "population" in df.columns and "median_household_income" in df.columns:
            # Calculate per capita income
            df["per_capita_income"] = df["median_household_income"] / (df["population"] / 100000)

        # Add metadata
        df["source_system"] = "census_acs_api"
        df["collected_at"] = pd.Timestamp.now()

        return df
