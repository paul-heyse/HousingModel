"""Base PermitsConnector class with pluggable architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import List, Optional, Union

from aker_core.cache import RateLimiter
from aker_core.logging import get_logger
from aker_core.run import RunContext

from .models import PermitCollectionResult, PermitRecord


class PermitsConnector(ABC):
    """Base class for permit portal connectors."""

    def __init__(
        self,
        city: str,
        state: str,
        run_context: Optional[RunContext] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """Initialize permit connector.

        Args:
            city: City name
            state: State abbreviation
            run_context: Optional RunContext for lineage tracking
            rate_limiter: Optional rate limiter for API calls
        """
        self.city = city
        self.state = state
        self.run_context = run_context
        self.rate_limiter = rate_limiter or RateLimiter(f"permits_{city}_{state}")
        self.logger = get_logger(f"permits.{city.lower()}_{state.lower()}")

        # 3-year rolling window configuration
        self.rolling_window_years = 3
        self.default_start_date = datetime.now() - timedelta(days=self.rolling_window_years * 365)

    @abstractmethod
    def fetch_permits(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        permit_types: Optional[List[str]] = None,
    ) -> PermitCollectionResult:
        """Fetch permits for the configured jurisdiction.

        Args:
            start_date: Start date for permit collection (default: 3 years ago)
            end_date: End date for permit collection (default: today)
            permit_types: Optional list of permit types to filter by

        Returns:
            PermitCollectionResult with collected permits and metadata
        """
        pass

    def get_supported_permit_types(self) -> List[str]:
        """Get list of supported permit types for this connector.

        Returns:
            List of permit type strings
        """
        return [pt.value for pt in self.get_permit_type_enum()]

    @abstractmethod
    def get_permit_type_enum(self) -> type:
        """Get the permit type enum for this connector.

        Returns:
            Enum class for permit types
        """
        pass

    def get_supported_date_range(self) -> tuple[date, date]:
        """Get the supported date range for this connector.

        Returns:
            Tuple of (earliest_date, latest_date)
        """
        return (self.default_start_date.date(), datetime.now().date())

    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """Validate that date range is within supported limits.

        Args:
            start_date: Start date to validate
            end_date: End date to validate

        Returns:
            True if date range is valid
        """
        earliest, latest = self.get_supported_date_range()

        if start_date < earliest:
            self.logger.warning(f"Start date {start_date} is before supported range {earliest}")
            return False

        if end_date > latest:
            self.logger.warning(f"End date {end_date} is after supported range {latest}")
            return False

        if start_date > end_date:
            self.logger.warning(f"Start date {start_date} is after end date {end_date}")
            return False

        return True

    def normalize_permit_data(self, raw_permits: List[dict]) -> List[PermitRecord]:
        """Normalize raw permit data into standardized PermitRecord objects.

        Args:
            raw_permits: List of raw permit dictionaries

        Returns:
            List of standardized PermitRecord objects
        """
        normalized = []

        for raw_permit in raw_permits:
            try:
                permit_record = self._convert_to_permit_record(raw_permit)
                normalized.append(permit_record)
            except Exception as e:
                self.logger.error(
                    f"Failed to normalize permit {raw_permit.get('id', 'unknown')}: {e}"
                )
                # Log processing error
                if self.run_context:
                    self.run_context.log_data_lake_operation(
                        operation="permit_normalization_error",
                        dataset=f"permits_{self.city}_{self.state}",
                        path=str(raw_permit.get("id", "unknown")),
                        metadata={"error": str(e)},
                    )

        return normalized

    def _convert_to_permit_record(self, raw_permit: dict) -> PermitRecord:
        """Convert raw permit data to standardized PermitRecord.

        Subclasses should override this. The default implementation raises to
        make the requirement explicit while still allowing simple test doubles.
        """

        raise NotImplementedError("Connector must implement _convert_to_permit_record")

    def _create_address(self, address_data: dict) -> "Address":
        """Create Address object from raw address data."""
        from .models import Address

        return Address(
            street=address_data.get("street", ""),
            city=address_data.get("city", self.city),
            state=address_data.get("state", self.state),
            zip_code=address_data.get("zip_code", ""),
            county=address_data.get("county"),
            latitude=address_data.get("latitude"),
            longitude=address_data.get("longitude"),
        )

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string into date object."""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

            # Try parsing as datetime and convert to date
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.date()

        except Exception:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def _parse_float(self, value: Union[str, float, int, None]) -> Optional[float]:
        """Parse value to float with error handling."""
        if value is None or value == "":
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse float: {value}")
            return None

    def _parse_int(self, value: Union[str, int, None]) -> Optional[int]:
        """Parse value to int with error handling."""
        if value is None or value == "":
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse int: {value}")
            return None

    def _log_collection_start(self, start_date: date, end_date: date):
        """Log the start of permit collection."""
        self.logger.info(
            f"Starting permit collection for {self.city}, {self.state}",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="permit_collection_start",
                dataset=f"permits_{self.city}_{self.state}",
                path=f"{start_date.isoformat()}_to_{end_date.isoformat()}",
                metadata={
                    "city": self.city,
                    "state": self.state,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

    def _log_collection_complete(self, result: PermitCollectionResult):
        """Log the completion of permit collection."""
        self.logger.info(
            f"Completed permit collection for {self.city}, {self.state}",
            total_permits=result.total_permits,
            errors=len(result.errors),
            success=result.success,
        )

        if self.run_context:
            self.run_context.log_data_lake_operation(
                operation="permit_collection_complete",
                dataset=f"permits_{self.city}_{self.state}",
                path="collection_result",
                metadata=result.to_dict(),
            )


def get_connector(
    city: str, state: str, run_context: Optional[RunContext] = None
) -> PermitsConnector:
    """Get the appropriate connector for a city/state combination.

    Args:
        city: City name
        state: State abbreviation
        run_context: Optional RunContext for lineage tracking

    Returns:
        PermitsConnector instance for the specified jurisdiction
    """
    from .registry import ConnectorRegistry

    registry = ConnectorRegistry()
    return registry.get_connector(city, state, run_context)
