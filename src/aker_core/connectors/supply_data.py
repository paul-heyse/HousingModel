"""
Data connectors for supply constraint metrics.

Provides interfaces to external data sources for building permits, household estimates,
HUD vacancy data, and lease transaction information.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..cache import Cache, RateLimiter
from .base import BaseConnector

logger = logging.getLogger(__name__)


@dataclass
class BuildingPermitData:
    """Building permit data structure."""

    msa_id: str
    year: int
    permits_issued: int
    source: str
    data_date: date


@dataclass
class HouseholdEstimate:
    """Household estimate data structure."""

    msa_id: str
    year: int
    households: int
    source: str
    data_date: date


@dataclass
class HUDVacancyData:
    """HUD vacancy rate data structure."""

    msa_id: str
    year: int
    vacancy_rate: float
    vacancy_type: str  # 'rental', 'multifamily', 'overall'
    source: str
    data_date: date


@dataclass
class LeaseTransaction:
    """Lease transaction data structure."""

    msa_id: str
    property_id: str
    lease_date: date
    days_on_market: int
    property_type: str
    source: str
    data_date: date


class HUDConnector(BaseConnector):
    """Connector for HUD vacancy data."""

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        """Initialize HUD connector."""
        super().__init__("HUD")
        self.api_key = api_key
        self.cache = Cache(ttl=cache_ttl)
        self.rate_limiter = RateLimiter(calls_per_minute=60)

    def get_vacancy_data(
        self, msa_ids: List[str], start_year: int = 2010, end_year: Optional[int] = None
    ) -> List[HUDVacancyData]:
        """
        Get HUD vacancy data for specified MSAs.

        Args:
            msa_ids: List of MSA identifiers
            start_year: Start year for data
            end_year: End year for data (default: current year)

        Returns:
            List of HUD vacancy data records
        """
        if end_year is None:
            end_year = datetime.now().year

        all_data = []

        for msa_id in msa_ids:
            cache_key = f"hud_vacancy_{msa_id}_{start_year}_{end_year}"

            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached HUD data for MSA {msa_id}")
                all_data.extend(cached_data)
                continue

            try:
                self.rate_limiter.wait_if_needed()

                # In production, this would make actual API calls to HUD
                # For now, return mock data
                mock_data = self._get_mock_hud_data(msa_id, start_year, end_year)
                all_data.extend(mock_data)

                self.cache.set(cache_key, mock_data)

            except Exception as e:
                logger.error(f"Failed to fetch HUD data for MSA {msa_id}: {e}")
                # Return empty list for this MSA
                continue

        return all_data

    def _get_mock_hud_data(
        self, msa_id: str, start_year: int, end_year: int
    ) -> List[HUDVacancyData]:
        """Get mock HUD data for testing."""
        mock_data = []

        # Generate realistic mock data
        base_vacancy = 5.0  # Base vacancy rate
        trend = -0.2  # Slight downward trend

        for year in range(start_year, end_year + 1):
            vacancy_rate = base_vacancy + (year - start_year) * trend
            vacancy_rate = max(2.0, min(15.0, vacancy_rate))  # Keep in reasonable range

            mock_data.append(
                HUDVacancyData(
                    msa_id=msa_id,
                    year=year,
                    vacancy_rate=round(vacancy_rate, 2),
                    vacancy_type="rental",
                    source="HUD",
                    data_date=datetime.now().date(),
                )
            )

        return mock_data


class CensusConnector(BaseConnector):
    """Connector for Census Bureau data (household estimates, etc.)."""

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        """Initialize Census connector."""
        super().__init__("Census")
        self.api_key = api_key
        self.cache = Cache(ttl=cache_ttl)
        self.rate_limiter = RateLimiter(calls_per_minute=1000)  # Census allows higher rate

    def get_household_estimates(
        self, msa_ids: List[str], start_year: int = 2010, end_year: Optional[int] = None
    ) -> List[HouseholdEstimate]:
        """
        Get household estimates from Census Bureau.

        Args:
            msa_ids: List of MSA identifiers
            start_year: Start year for data
            end_year: End year for data (default: current year)

        Returns:
            List of household estimate records
        """
        if end_year is None:
            end_year = datetime.now().year

        all_data = []

        for msa_id in msa_ids:
            cache_key = f"census_households_{msa_id}_{start_year}_{end_year}"

            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached Census data for MSA {msa_id}")
                all_data.extend(cached_data)
                continue

            try:
                self.rate_limiter.wait_if_needed()

                # In production, this would make actual API calls to Census
                # For now, return mock data
                mock_data = self._get_mock_household_data(msa_id, start_year, end_year)
                all_data.extend(mock_data)

                self.cache.set(cache_key, mock_data)

            except Exception as e:
                logger.error(f"Failed to fetch Census data for MSA {msa_id}: {e}")
                continue

        return all_data

    def _get_mock_household_data(
        self, msa_id: str, start_year: int, end_year: int
    ) -> List[HouseholdEstimate]:
        """Get mock Census household data."""
        mock_data = []

        # Generate realistic mock data with growth
        base_households = 50000  # Base household count
        growth_rate = 0.01  # 1% annual growth

        for year in range(start_year, end_year + 1):
            households = int(base_households * (1 + growth_rate) ** (year - start_year))

            mock_data.append(
                HouseholdEstimate(
                    msa_id=msa_id,
                    year=year,
                    households=households,
                    source="Census_ACS",
                    data_date=datetime.now().date(),
                )
            )

        return mock_data


class PermitPortalConnector(BaseConnector):
    """Connector for local building permit portals."""

    def __init__(self, cache_ttl: int = 3600):
        """Initialize permit portal connector."""
        super().__init__("PermitPortals")
        self.cache = Cache(ttl=cache_ttl)
        self.rate_limiter = RateLimiter(calls_per_minute=30)  # Conservative rate for local APIs

    def get_building_permits(
        self, msa_ids: List[str], start_year: int = 2010, end_year: Optional[int] = None
    ) -> List[BuildingPermitData]:
        """
        Get building permit data from local permit portals.

        Args:
            msa_ids: List of MSA identifiers
            start_year: Start year for data
            end_year: End year for data (default: current year)

        Returns:
            List of building permit records
        """
        if end_year is None:
            end_year = datetime.now().year

        all_data = []

        for msa_id in msa_ids:
            cache_key = f"permits_{msa_id}_{start_year}_{end_year}"

            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached permit data for MSA {msa_id}")
                all_data.extend(cached_data)
                continue

            try:
                self.rate_limiter.wait_if_needed()

                # In production, this would scrape or call local permit APIs
                # For now, return mock data
                mock_data = self._get_mock_permit_data(msa_id, start_year, end_year)
                all_data.extend(mock_data)

                self.cache.set(cache_key, mock_data)

            except Exception as e:
                logger.error(f"Failed to fetch permit data for MSA {msa_id}: {e}")
                continue

        return all_data

    def _get_mock_permit_data(
        self, msa_id: str, start_year: int, end_year: int
    ) -> List[BuildingPermitData]:
        """Get mock building permit data."""
        mock_data = []

        # Generate realistic mock data with some volatility
        base_permits = 1000
        volatility = 0.1  # 10% volatility

        for year in range(start_year, end_year + 1):
            # Add some randomness to simulate real market conditions
            random_factor = np.random.normal(1.0, volatility)
            permits = int(base_permits * random_factor)

            mock_data.append(
                BuildingPermitData(
                    msa_id=msa_id,
                    year=year,
                    permits_issued=permits,
                    source="Local_Permit_Portal",
                    data_date=datetime.now().date(),
                )
            )

        return mock_data


class LeaseDataConnector(BaseConnector):
    """Connector for lease transaction data from property management systems."""

    def __init__(self, cache_ttl: int = 1800):  # Shorter cache for more dynamic data
        """Initialize lease data connector."""
        super().__init__("LeaseData")
        self.cache = Cache(ttl=cache_ttl)
        self.rate_limiter = RateLimiter(calls_per_minute=120)

    def get_lease_transactions(
        self,
        msa_ids: List[str],
        start_date: date,
        end_date: Optional[date] = None,
        property_types: Optional[List[str]] = None,
    ) -> List[LeaseTransaction]:
        """
        Get lease transaction data.

        Args:
            msa_ids: List of MSA identifiers
            start_date: Start date for lease data
            end_date: End date for lease data (default: today)
            property_types: Filter by property types

        Returns:
            List of lease transaction records
        """
        if end_date is None:
            end_date = datetime.now().date()

        all_data = []

        for msa_id in msa_ids:
            cache_key = f"leases_{msa_id}_{start_date}_{end_date}"

            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached lease data for MSA {msa_id}")
                all_data.extend(cached_data)
                continue

            try:
                self.rate_limiter.wait_if_needed()

                # In production, this would query property management databases
                # For now, return mock data
                mock_data = self._get_mock_lease_data(msa_id, start_date, end_date, property_types)
                all_data.extend(mock_data)

                self.cache.set(cache_key, mock_data)

            except Exception as e:
                logger.error(f"Failed to fetch lease data for MSA {msa_id}: {e}")
                continue

        return all_data

    def _get_mock_lease_data(
        self,
        msa_id: str,
        start_date: date,
        end_date: date,
        property_types: Optional[List[str]] = None,
    ) -> List[LeaseTransaction]:
        """Get mock lease transaction data."""
        mock_data = []

        # Generate realistic lease data
        num_leases = 100  # Mock sample size
        base_days_on_market = 30  # Base lease-up time

        current_date = start_date
        while current_date <= end_date and len(mock_data) < num_leases:
            # Generate lease date
            lease_date = current_date

            # Generate days on market (normal distribution around base)
            days_on_market = max(1, int(np.random.normal(base_days_on_market, 10)))

            # Generate property type
            property_type = np.random.choice(["apartment", "condo", "townhouse", "single_family"])

            # Filter by property types if specified
            if property_types and property_type not in property_types:
                current_date += pd.Timedelta(days=1)
                continue

            mock_data.append(
                LeaseTransaction(
                    msa_id=msa_id,
                    property_id=f"PROP_{len(mock_data):03d}",
                    lease_date=lease_date,
                    days_on_market=days_on_market,
                    property_type=property_type,
                    source="Property_Management_System",
                    data_date=datetime.now().date(),
                )
            )

            current_date += pd.Timedelta(days=1)

        return mock_data


class SupplyDataETL:
    """ETL processor for supply constraint data."""

    def __init__(self):
        """Initialize ETL processor."""
        self.hud_connector = HUDConnector()
        self.census_connector = CensusConnector()
        self.permit_connector = PermitPortalConnector()
        self.lease_connector = LeaseDataConnector()

    def extract_supply_data(
        self, msa_ids: List[str], start_year: int = 2010, end_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract supply data from all sources.

        Args:
            msa_ids: List of MSA identifiers
            start_year: Start year for data
            end_year: End year for data

        Returns:
            Dictionary with all extracted data
        """
        logger.info(f"Extracting supply data for {len(msa_ids)} MSAs")

        # Extract building permits
        permit_data = self.permit_connector.get_building_permits(msa_ids, start_year, end_year)

        # Extract household estimates
        household_data = self.census_connector.get_household_estimates(
            msa_ids, start_year, end_year
        )

        # Extract HUD vacancy data
        hud_data = self.hud_connector.get_vacancy_data(msa_ids, start_year, end_year)

        # Extract lease data (last 2 years for recency)
        lease_start = datetime.now().date().replace(year=datetime.now().year - 2)
        lease_data = self.lease_connector.get_lease_transactions(
            msa_ids, lease_start, datetime.now().date()
        )

        return {
            "permits": permit_data,
            "households": household_data,
            "vacancy": hud_data,
            "leases": lease_data,
            "extraction_timestamp": datetime.now().isoformat(),
            "msa_count": len(msa_ids),
            "data_years": f"{start_year}-{end_year or datetime.now().year}",
        }

    def transform_supply_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw supply data into calculation-ready format.

        Args:
            raw_data: Raw data from extract step

        Returns:
            Transformed data ready for calculations
        """
        logger.info("Transforming supply data")

        # Group permits by MSA and year
        permits_by_msa = {}
        for permit in raw_data["permits"]:
            if permit.msa_id not in permits_by_msa:
                permits_by_msa[permit.msa_id] = {}
            permits_by_msa[permit.msa_id][permit.year] = permit.permits_issued

        # Group households by MSA and year
        households_by_msa = {}
        for household in raw_data["households"]:
            if household.msa_id not in households_by_msa:
                households_by_msa[household.msa_id] = {}
            households_by_msa[household.msa_id][household.year] = household.households

        # Group vacancy data by MSA
        vacancy_by_msa = {}
        for vacancy_record in raw_data["vacancy"]:
            if vacancy_record.msa_id not in vacancy_by_msa:
                vacancy_by_msa[vacancy_record.msa_id] = []
            vacancy_by_msa[vacancy_record.msa_id].append(
                {
                    "year": vacancy_record.year,
                    "vacancy_rate": vacancy_record.vacancy_rate,
                    "vacancy_type": vacancy_record.vacancy_type,
                    "source": vacancy_record.source,
                }
            )

        # Group lease data by MSA
        leases_by_msa = {}
        for lease in raw_data["leases"]:
            if lease.msa_id not in leases_by_msa:
                leases_by_msa[lease.msa_id] = []
            leases_by_msa[lease.msa_id].append(
                {
                    "lease_date": lease.lease_date,
                    "days_on_market": lease.days_on_market,
                    "property_type": lease.property_type,
                }
            )

        return {
            "permits_by_msa": permits_by_msa,
            "households_by_msa": households_by_msa,
            "vacancy_by_msa": vacancy_by_msa,
            "leases_by_msa": leases_by_msa,
            "transformation_timestamp": datetime.now().isoformat(),
            "data_quality": self._assess_data_quality(raw_data),
        }

    def _assess_data_quality(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data quality of extracted data."""
        quality_metrics = {
            "permits_records": len(raw_data["permits"]),
            "households_records": len(raw_data["households"]),
            "vacancy_records": len(raw_data["vacancy"]),
            "leases_records": len(raw_data["leases"]),
            "unique_msas": len(set([p.msa_id for p in raw_data["permits"]])),
            "data_completeness": 0.0,
        }

        # Calculate completeness score
        total_expected = (
            len(raw_data["permits"]) + len(raw_data["households"]) + len(raw_data["vacancy"])
        )
        if total_expected > 0:
            quality_metrics["data_completeness"] = len(raw_data["leases"]) / total_expected

        return quality_metrics

    def load_supply_data(self, transformed_data: Dict[str, Any], session) -> Dict[str, Any]:
        """
        Load transformed supply data into database.

        Args:
            transformed_data: Transformed data from transform step
            session: Database session

        Returns:
            Loading results
        """
        from ..supply.integration import calculate_supply_metrics

        logger.info("Loading supply data to database")

        results = {"successful_loads": 0, "failed_loads": 0, "errors": []}

        for msa_id in transformed_data["permits_by_msa"]:
            try:
                # Prepare data for calculation
                permits = list(transformed_data["permits_by_msa"][msa_id].values())
                households = list(transformed_data["households_by_msa"][msa_id].values())
                hud_data = transformed_data["vacancy_by_msa"].get(msa_id, [])
                lease_data = transformed_data["leases_by_msa"].get(msa_id, [])

                # Convert lease data to expected format
                lease_data_formatted = {
                    "lease_date": [lease["lease_date"] for lease in lease_data],
                    "property_id": [f"PROP_{i}" for i in range(len(lease_data))],
                    "days_on_market": [lease["days_on_market"] for lease in lease_data],
                }

                # Calculate and persist metrics
                calculate_supply_metrics(
                    session=session,
                    msa_id=msa_id,
                    permits_data=permits,
                    households_data=households,
                    hud_vacancy_data={
                        "year": [h["year"] for h in hud_data],
                        "vacancy_rate": [h["vacancy_rate"] for h in hud_data],
                        "geography": [msa_id] * len(hud_data),
                    },
                    lease_data=lease_data_formatted,
                    data_vintage=datetime.now().strftime("%Y-%m-%d"),
                )

                results["successful_loads"] += 1
                logger.info(f"Successfully loaded data for MSA {msa_id}")

            except Exception as e:
                results["failed_loads"] += 1
                results["errors"].append(f"MSA {msa_id}: {str(e)}")
                logger.error(f"Failed to load data for MSA {msa_id}: {e}")

        return results
