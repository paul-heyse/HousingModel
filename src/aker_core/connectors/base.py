"""Base connector classes for data source integration."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aker_core.cache import RateLimiter
from aker_core.logging import get_logger
from aker_core.run import RunContext


class BaseConnector:
    """Base class for all data connectors."""

    def __init__(
        self,
        name: str,
        base_url: str,
        rate_limiter: Optional[RateLimiter] = None,
        run_context: Optional[RunContext] = None,
    ):
        """Initialize base connector.

        Args:
            name: Connector name
            base_url: Base URL for API requests
            rate_limiter: Optional rate limiter for API calls
            run_context: Optional RunContext for lineage tracking
        """
        self.name = name
        self.base_url = base_url
        self.rate_limiter = rate_limiter or RateLimiter(f"connector_{name}")
        self.run_context = run_context
        self.logger = get_logger(f"connectors.{name}")

        # HTTP session with retry configuration
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None, **kwargs
    ) -> pd.DataFrame:
        """Fetch data from the source.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters

        Returns:
            DataFrame with collected data
        """
        raise NotImplementedError("BaseConnector.fetch_data must be implemented by subclasses")

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
    ) -> requests.Response:
        """Make HTTP request with rate limiting and error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            method: HTTP method

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"

        # Apply rate limiting
        self.rate_limiter._wait_for_token()

        try:
            response = self.session.request(
                method=method, url=url, params=params, headers=headers, timeout=30
            )

            # Log successful request
            self.logger.info(
                f"API request successful: {method} {url}",
                status_code=response.status_code,
                response_size=len(response.content) if response.content else 0,
            )

            return response

        except requests.RequestException as e:
            self.logger.error(f"API request failed: {method} {url}", error=str(e))
            raise

    def _log_collection_start(self, start_date: date, end_date: date, **metadata):
        """Log the start of data collection."""
        self.logger.info(
            f"Starting data collection for {self.name}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            **metadata,
        )

        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="data_collection_start",
                dataset=f"connector_{self.name}",
                path=f"{start_date.isoformat()}_to_{end_date.isoformat()}",
                metadata={
                    "connector": self.name,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    **metadata,
                },
            )

    def _log_collection_complete(self, result: Any, **metadata):
        """Log the completion of data collection."""
        self.logger.info(
            f"Completed data collection for {self.name}",
            result_type=type(result).__name__,
            **metadata,
        )

        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="data_collection_complete",
                dataset=f"connector_{self.name}",
                path="collection_result",
                metadata={"connector": self.name, "result_type": type(result).__name__, **metadata},
            )

    def _validate_date_range(self, start_date: date, end_date: date) -> bool:
        """Validate that date range is reasonable."""
        if start_date > end_date:
            self.logger.warning(f"Start date {start_date} is after end date {end_date}")
            return False

        # Check for reasonable date ranges (not too far in the past/future)
        today = date.today()
        max_days_back = 365 * 10  # 10 years
        min_start_date = today - timedelta(days=max_days_back)

        if start_date < min_start_date:
            self.logger.warning(
                f"Start date {start_date} is more than {max_days_back} days in the past"
            )
            return False

        return True


class DataConnector(BaseConnector):
    """Base class for data source connectors that return structured data."""

    def __init__(self, name: str, base_url: str, output_schema: Dict[str, str], **kwargs):
        """Initialize data connector.

        Args:
            name: Connector name
            base_url: Base URL for API requests
            output_schema: Expected output column schema
            **kwargs: Additional arguments for BaseConnector
        """
        super().__init__(name, base_url, **kwargs)
        self.output_schema = output_schema

    def fetch_data(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None, **kwargs
    ) -> pd.DataFrame:
        """Fetch data and return as DataFrame.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters

        Returns:
            DataFrame with collected data
        """
        # Set default date range
        if start_date is None:
            start_date = date.today() - timedelta(days=365)  # 1 year back
        if end_date is None:
            end_date = date.today()

        # Validate date range
        if not self._validate_date_range(start_date, end_date):
            raise ValueError(f"Invalid date range: {start_date} to {end_date}")

        self._log_collection_start(start_date, end_date, **kwargs)

        try:
            # Fetch raw data
            raw_data = self._fetch_raw_data(start_date, end_date, **kwargs)

            # Transform to DataFrame
            df = self._transform_to_dataframe(raw_data)

            # Validate schema
            self._validate_dataframe_schema(df)

            self._log_collection_complete(df, rows=len(df))
            return df

        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            raise

    def _fetch_raw_data(self, start_date: date, end_date: date, **kwargs) -> Any:
        """Fetch raw data from the source.

        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            **kwargs: Additional parameters

        Returns:
            Raw data from the source
        """
        raise NotImplementedError("DataConnector subclasses must implement _fetch_raw_data")

    def _transform_to_dataframe(self, raw_data: Any) -> pd.DataFrame:
        """Transform raw data to DataFrame.

        Args:
            raw_data: Raw data from the source

        Returns:
            DataFrame with standardized format
        """
        if isinstance(raw_data, pd.DataFrame):
            return raw_data

        if isinstance(raw_data, dict):
            return pd.DataFrame(raw_data)

        if isinstance(raw_data, list):
            return pd.DataFrame(raw_data)

        raise ValueError(f"Cannot transform raw data of type {type(raw_data)} to DataFrame")

    def _validate_dataframe_schema(self, df: pd.DataFrame) -> None:
        """Validate DataFrame schema matches expected output schema.

        Args:
            df: DataFrame to validate

        Raises:
            ValueError: If schema validation fails
        """
        missing_columns = set(self.output_schema.keys()) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing expected columns: {missing_columns}")

        # Check data types (basic validation)
        for col, expected_type in self.output_schema.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if expected_type not in actual_dtype.lower():
                    self.logger.warning(
                        f"Column {col} has dtype {actual_dtype}, expected {expected_type}"
                    )
