"""Los Angeles permit portal connector."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from aker_core.cache import fetch
from aker_core.run import RunContext

from ..connector import PermitsConnector
from ..models import PermitCollectionResult, PermitRecord, PermitStatus, PermitType


class LAConnector(PermitsConnector):
    """Connector for Los Angeles permit portal."""

    def __init__(
        self,
        city: str = "Los Angeles",
        state: str = "CA",
        run_context: Optional[RunContext] = None,
        **kwargs,
    ):
        """Initialize LA connector."""
        super().__init__(
            city, state, run_context=run_context, rate_limiter=kwargs.get("rate_limiter")
        )
        self.base_url = "https://data.lacity.org/resource"
        self.api_key = kwargs.get("api_key")  # LA Open Data API key if needed

    def get_permit_type_enum(self) -> type:
        """Get LA-specific permit types."""
        return LAPermitType

    def fetch_permits(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        permit_types: Optional[List[str]] = None,
    ) -> PermitCollectionResult:
        """Fetch permits from LA Open Data API."""
        # Set default date range
        if start_date is None:
            start_date = self.default_start_date.date()
        if end_date is None:
            end_date = date.today()

        # Validate date range
        if not self.validate_date_range(start_date, end_date):
            return PermitCollectionResult([], {"error": "Invalid date range"})

        self._log_collection_start(start_date, end_date)

        permits = []
        errors = []

        try:
            # LA Building and Safety permits API endpoint
            endpoint = f"{self.base_url}/3p5m-x26h.json"

            # Build query parameters
            params = {
                "issue_date": f"{start_date}T00:00:00..{end_date}T23:59:59",
                "$limit": 50000,  # Reasonable limit for API
            }

            # Add permit type filter if specified
            if permit_types:
                # Map our permit types to LA categories
                la_types = []
                for pt in permit_types:
                    if pt in [t.value for t in self.get_permit_type_enum()]:
                        la_types.append(self._map_permit_type_to_la(pt))
                if la_types:
                    params["permit_type"] = ",".join(la_types)

            # Fetch data with caching
            response = fetch(endpoint, params=params, ttl="1d")

            if response.status_code != 200:
                errors.append(f"API returned {response.status_code}: {response.text}")
                return PermitCollectionResult(permits, {"errors": errors})

            raw_data = response.json()

            # Normalize to our standard format
            permits = self.normalize_permit_data(raw_data)

            self._log_collection_complete(
                PermitCollectionResult(permits, {"records_fetched": len(raw_data)})
            )

            return PermitCollectionResult(permits, {"records_fetched": len(raw_data)})

        except Exception as e:
            errors.append(f"Failed to fetch permits: {e}")
            self.logger.error(f"Permit collection failed: {e}")
            return PermitCollectionResult(permits, {"errors": errors})

    def _convert_to_permit_record(self, raw_permit: dict) -> PermitRecord:
        """Convert LA permit data to standardized format."""
        # Extract and parse dates
        issue_date = self._parse_date(raw_permit.get("issue_date", ""))
        application_date = self._parse_date(raw_permit.get("application_date", ""))
        expiration_date = self._parse_date(raw_permit.get("expiration_date", ""))

        # Determine permit type
        permit_type_str = raw_permit.get("permit_type", "")
        permit_type = self._map_la_permit_type_to_permit_type(permit_type_str)

        # Determine status
        status = raw_permit.get("status", "")
        permit_status = self._map_la_status_to_permit_status(status)

        # Parse financial data
        estimated_cost = self._parse_float(raw_permit.get("estimated_cost", ""))
        valuation = self._parse_float(raw_permit.get("valuation", ""))

        # Create address
        address_data = {
            "street": raw_permit.get("address", ""),
            "city": self.city,
            "state": self.state,
            "zip_code": raw_permit.get("zip_code", ""),
        }

        return PermitRecord(
            permit_id=str(raw_permit.get("permit_number", "")),
            permit_type=permit_type,
            status=permit_status,
            description=raw_permit.get("description", ""),
            application_date=application_date or date.today(),
            issue_date=issue_date,
            expiration_date=expiration_date,
            estimated_cost=estimated_cost,
            valuation=valuation,
            address=address_data,
            property_type=raw_permit.get("occupancy_type", "unknown"),
            applicant_name=raw_permit.get("applicant_name", ""),
            contractor_name=raw_permit.get("contractor_name", ""),
            contractor_license=raw_permit.get("contractor_license", ""),
            source_system="la_building_safety_api",
            source_url=f"{self.base_url}/3p5m-x26h.json",
        )

    def _map_permit_type_to_la(self, permit_type: str) -> str:
        """Map our permit types to LA permit types."""
        mapping = {
            "residential_new": "Bldg-New",
            "residential_renovation": "Bldg-Alter/Repair",
            "commercial_new": "Bldg-New",
            "commercial_renovation": "Bldg-Alter/Repair",
            "demolition": "Bldg-Demolition",
            "addition": "Bldg-Addition",
            "pool": "Pool/Spa",
            "garage": "Garage",
        }
        return mapping.get(permit_type, "Bldg-Alter/Repair")

    def _map_la_permit_type_to_permit_type(self, la_type: str) -> PermitType:
        """Map LA permit type to our permit type enum."""
        mapping = {
            "Bldg-New": PermitType.RESIDENTIAL_NEW,
            "Bldg-Alter/Repair": PermitType.RESIDENTIAL_RENOVATION,
            "Bldg-Demolition": PermitType.DEMOLITION,
            "Bldg-Addition": PermitType.ADDITION,
            "Pool/Spa": PermitType.POOL,
            "Garage": PermitType.GARAGE,
        }
        return mapping.get(la_type, PermitType.OTHER)

    def _map_la_status_to_permit_status(self, status: str) -> PermitStatus:
        """Map LA status to our permit status enum."""
        status_lower = status.lower()

        if "issued" in status_lower or "approved" in status_lower:
            return PermitStatus.ISSUED
        elif "denied" in status_lower or "rejected" in status_lower:
            return PermitStatus.DENIED
        elif "finaled" in status_lower or "completed" in status_lower:
            return PermitStatus.COMPLETED
        elif "expired" in status_lower:
            return PermitStatus.EXPIRED
        elif "cancelled" in status_lower:
            return PermitStatus.CANCELLED
        else:
            return PermitStatus.PENDING


class LAPermitType:
    """LA-specific permit type constants."""

    BUILDING_NEW = "Bldg-New"
    BUILDING_ALTER_REPAIR = "Bldg-Alter/Repair"
    BUILDING_DEMOLITION = "Bldg-Demolition"
    BUILDING_ADDITION = "Bldg-Addition"
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    MECHANICAL = "Mechanical"
    POOL_SPA = "Pool/Spa"
    GRADING = "Grading"
    FIRE_SPRINKLER = "Fire Sprinkler"
    GARAGE = "Garage"
    FENCE = "Fence"
    SIGN = "Sign"
