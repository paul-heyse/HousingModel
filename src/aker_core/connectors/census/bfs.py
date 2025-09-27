"""Census BFS (Business Formation Statistics) data connector."""

from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd

from aker_core.cache import fetch

from ..base import DataConnector


class BFSConnector(DataConnector):
    """Connector for US Census Bureau Business Formation Statistics (BFS) data."""

    def __init__(self, **kwargs):
        """Initialize BFS connector."""
        super().__init__(
            name="bfs",
            base_url="https://api.census.gov/data",
            output_schema={
                "state": "string",
                "state_fips": "string",
                "msa_id": "string",
                "msa_name": "string",
                "business_applications": "int64",
                "business_formations": "int64",
                "business_formation_rate": "float64",
                "data_year": "int64",
                "data_month": "int64",
                "collected_at": "datetime64[ns]",
            },
            **kwargs,
        )
        self.api_key = kwargs.get("api_key")

    def _fetch_raw_data(self, start_date: date, end_date: date, **kwargs) -> pd.DataFrame:
        """Fetch BFS data from Census API."""
        # BFS data is typically available at state and MSA levels
        # For now, fetch state-level data
        states = kwargs.get(
            "states",
            [
                "01",
                "02",
                "04",
                "05",
                "06",
                "08",
                "09",
                "10",
                "11",
                "12",
                "13",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
                "21",
                "22",
                "23",
                "24",
                "25",
                "26",
                "27",
                "28",
                "29",
                "30",
                "31",
                "32",
                "33",
                "34",
                "35",
                "36",
                "37",
                "38",
                "39",
                "40",
                "41",
                "42",
                "44",
                "45",
                "46",
                "47",
                "48",
                "49",
                "50",
                "51",
                "53",
                "54",
                "55",
                "56",
            ],
        )

        all_data = []

        # Fetch data for each state
        for state_fips in states:
            try:
                state_data = self._fetch_state_data(state_fips, start_date.year, end_date.year)
                if state_data:
                    all_data.extend(state_data)
            except Exception as e:
                self.logger.error(f"Failed to fetch data for state {state_fips}: {e}")

        if not all_data:
            raise ValueError("No BFS data retrieved from Census API")

        return pd.DataFrame(all_data)

    def _fetch_state_data(self, state_fips: str, start_year: int, end_year: int) -> List[dict]:
        """Fetch BFS data for a specific state."""
        endpoint = f"/{start_year}/bfs/bfs"

        params = {
            "get": "NAME,BUSINESS_APPLICATIONS,BUSINESS_FORMATIONS,BF_SAF",
            "for": f"state:{state_fips}",
            "time": f"from {start_year} to {end_year}",
            "$limit": 50000,
        }

        if self.api_key:
            params["key"] = self.api_key

        response = fetch(endpoint, params=params, ttl="30d")

        if response.status_code != 200:
            self.logger.error(f"BFS API error for state {state_fips}: {response.status_code}")
            return []

        data = response.json()

        if len(data) <= 1:  # Header only or empty
            return []

        headers = data[0]
        rows = data[1:]

        state_data = []
        for row in rows:
            record = dict(zip(headers, row))

            state_record = {
                "state": record.get("NAME", ""),
                "state_fips": state_fips,
                "business_applications": self._parse_int(record.get("BUSINESS_APPLICATIONS")),
                "business_formations": self._parse_int(record.get("BUSINESS_FORMATIONS")),
                "data_year": start_year,  # Simplified - would need to parse time field
                "data_month": 12,  # Simplified
                "collected_at": pd.Timestamp.now(),
            }

            # Calculate formation rate if both values exist
            if state_record["business_applications"] and state_record["business_formations"]:
                state_record["business_formation_rate"] = (
                    state_record["business_formations"] / state_record["business_applications"]
                ) * 100

            state_data.append(state_record)

        return state_data

    def _transform_to_dataframe(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Transform BFS data to standardized format."""
        df = super()._transform_to_dataframe(raw_data)

        # Add metadata
        df["source_system"] = "census_bfs_api"
        df["collected_at"] = pd.Timestamp.now()

        return df
