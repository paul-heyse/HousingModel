"""New York City permit portal connector."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from aker_core.cache import fetch

from ..connector import PermitsConnector
from ..models import PermitCollectionResult, PermitRecord, PermitStatus, PermitType


class NYCConnector(PermitsConnector):
    """Connector for New York City permit portal."""

    def __init__(self, city: str = "New York", state: str = "NY", **kwargs):
        """Initialize NYC connector."""
        super().__init__(city, state, **kwargs)
        self.base_url = "https://data.cityofnewyork.us/resource"
        self.api_key = kwargs.get("api_key")  # NYC Open Data API key if needed

    def get_permit_type_enum(self) -> type:
        """Get NYC-specific permit types."""
        return NYCPermitType

    def fetch_permits(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        permit_types: Optional[List[str]] = None,
    ) -> PermitCollectionResult:
        """Fetch permits from NYC Open Data API."""
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
            # NYC DOB permits API endpoint
            endpoint = f"{self.base_url}/ipjk-dgnf.json"

            # Build query parameters
            params = {
                "filing_date": f"{start_date}T00:00:00..{end_date}T23:59:59",
                "$limit": 50000,  # Reasonable limit for API
            }

            # Add permit type filter if specified
            if permit_types:
                # Map our permit types to NYC categories
                nyc_types = []
                for pt in permit_types:
                    if pt in [t.value for t in self.get_permit_type_enum()]:
                        nyc_types.append(self._map_permit_type_to_nyc(pt))
                if nyc_types:
                    params["job_type"] = ",".join(nyc_types)

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
        """Convert NYC permit data to standardized format."""
        # Extract and parse dates
        filing_date = self._parse_date(raw_permit.get("filing_date", ""))
        issuance_date = self._parse_date(raw_permit.get("issuance_date", ""))
        expiration_date = self._parse_date(raw_permit.get("expiration_date", ""))

        # Determine permit type
        job_type = raw_permit.get("job_type", "")
        permit_type = self._map_nyc_job_type_to_permit_type(job_type)

        # Determine status
        status = raw_permit.get("status", "")
        permit_status = self._map_nyc_status_to_permit_status(status)

        # Parse financial data
        estimated_cost = self._parse_float(raw_permit.get("estimated_cost", ""))
        actual_cost = self._parse_float(raw_permit.get("actual_cost", ""))

        # Create address
        address_data = {
            "street": raw_permit.get("house_street", ""),
            "city": self.city,
            "state": self.state,
            "zip_code": raw_permit.get("zip_code", ""),
        }

        # Extract coordinates if available
        latitude = self._parse_float(raw_permit.get("latitude", ""))
        longitude = self._parse_float(raw_permit.get("longitude", ""))

        if latitude and longitude:
            address_data["latitude"] = latitude
            address_data["longitude"] = longitude

        return PermitRecord(
            permit_id=str(raw_permit.get("job_number", "")),
            permit_type=permit_type,
            status=permit_status,
            description=raw_permit.get("work_type", ""),
            application_date=filing_date or date.today(),
            issue_date=issuance_date,
            expiration_date=expiration_date,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            address=address_data,
            property_type=raw_permit.get("building_type", "unknown"),
            applicant_name=raw_permit.get("applicant_name", ""),
            contractor_name=raw_permit.get("contractor_name", ""),
            contractor_license=raw_permit.get("contractor_license", ""),
            source_system="nyc_dob_api",
            source_url=f"{self.base_url}/ipjk-dgnf.json",
        )

    def _map_permit_type_to_nyc(self, permit_type: str) -> str:
        """Map our permit types to NYC job types."""
        mapping = {
            "residential_new": "NB",  # New Building
            "residential_renovation": "A1",  # Alteration Type 1
            "commercial_new": "NB",
            "commercial_renovation": "A1",
            "demolition": "DM",
            "addition": "A1",
            "pool": "A1",
            "garage": "A1",
            "deck": "A1",
            "fence": "A1",
        }
        return mapping.get(permit_type, "A1")

    def _map_nyc_job_type_to_permit_type(self, job_type: str) -> PermitType:
        """Map NYC job type to our permit type enum."""
        mapping = {
            "NB": PermitType.RESIDENTIAL_NEW,
            "A1": PermitType.RESIDENTIAL_RENOVATION,
            "DM": PermitType.DEMOLITION,
        }
        return mapping.get(job_type, PermitType.OTHER)

    def _map_nyc_status_to_permit_status(self, status: str) -> PermitStatus:
        """Map NYC status to our permit status enum."""
        status_lower = status.lower()

        if "approved" in status_lower or "issued" in status_lower:
            return PermitStatus.APPROVED
        elif "denied" in status_lower or "rejected" in status_lower:
            return PermitStatus.DENIED
        elif "pending" in status_lower or "filed" in status_lower:
            return PermitStatus.PENDING
        elif "completed" in status_lower or "final" in status_lower:
            return PermitStatus.COMPLETED
        else:
            return PermitStatus.UNDER_REVIEW


class NYCPermitType:
    """NYC-specific permit type constants."""

    NEW_BUILDING = "NB"
    ALTERATION_1 = "A1"
    ALTERATION_2 = "A2"
    ALTERATION_3 = "A3"
    DEMOLITION = "DM"
    FOUNDATION = "FN"
    PLUMBING = "PL"
    SPRINKLER = "SP"
    STANDPIPE = "SD"
    SIGN = "SG"
    BOILER = "BL"
    ELEVATOR = "EL"
    ANTENNA = "AN"
