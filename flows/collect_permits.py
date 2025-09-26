"""Permit collection flow - collects permits from various city/state portals."""

from __future__ import annotations

import pandas as pd
from datetime import date, datetime
from prefect import flow, task
from typing import List, Optional

from aker_core.cache import get_cache
from aker_core.logging import get_logger
from aker_core.run import RunContext
from aker_core.validation import validate_data_quality
from aker_data.lake import DataLake
from aker_core.permits import get_connector, PermitRecord
from flows.base import ETLFlow, etl_task, timed_flow, with_run_context


class PermitCollectionFlow(ETLFlow):
    """Flow for collecting permits from various city/state portals."""

    def __init__(self):
        super().__init__("collect_permits", "Collect permits from city/state portals")

    @etl_task("fetch_permits_for_city", "Fetch permits for a specific city")
    def fetch_permits_for_city(
        self,
        city: str,
        state: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        permit_types: Optional[List[str]] = None
    ) -> List[PermitRecord]:
        """Fetch permits for a specific city."""
        self.logger.info(f"Fetching permits for {city}, {state}")

        try:
            connector = get_connector(city, state)
            result = connector.fetch_permits(start_date, end_date, permit_types)

            if not result.success:
                raise ValueError(f"Failed to fetch permits for {city}, {state}: {result.errors}")

            self.logger.info(f"Successfully fetched {len(result.permits)} permits for {city}, {state}")
            return result.permits

        except Exception as e:
            self.logger.error(f"Failed to fetch permits for {city}, {state}: {e}")
            raise

    @etl_task("validate_permit_data", "Validate collected permit data")
    def validate_permit_data(self, permits: List[PermitRecord]) -> bool:
        """Validate collected permit data."""
        if not permits:
            raise ValueError("No permits to validate")

        # Convert to DataFrame for validation
        df = pd.DataFrame([p.dict() for p in permits])

        # Use Great Expectations for comprehensive validation
        validation_result = validate_data_quality(
            df=df,
            suite_name="permits_validation",
            data_asset_name="collected_permits",
            fail_on_error=True
        )

        self.logger.info(f"Permit data validation passed: {validation_result['successful_expectations']}/{validation_result['total_expectations']} expectations")
        return True

    @etl_task("store_permit_data", "Store permit data in data lake")
    def store_permit_data(self, permits: List[PermitRecord], as_of: str) -> str:
        """Store permit data in data lake."""
        if not permits:
            raise ValueError("No permits to store")

        lake = DataLake()

        # Convert to DataFrame
        df = pd.DataFrame([p.dict() for p in permits])

        # Store in data lake with partitioning by state and year
        result_path = lake.write(
            df,
            dataset="permits",
            as_of=as_of,
            partition_by=["state"]
        )

        self.logger.info(f"Stored {len(permits)} permits to {result_path}")
        return result_path

    @etl_task("aggregate_permit_statistics", "Aggregate permit statistics")
    def aggregate_permit_statistics(self, permits: List[PermitRecord]) -> dict:
        """Aggregate permit statistics for reporting."""
        if not permits:
            return {}

        # Group by permit type and status
        type_counts = {}
        status_counts = {}

        for permit in permits:
            # Count by type
            permit_type = permit.permit_type.value
            type_counts[permit_type] = type_counts.get(permit_type, 0) + 1

            # Count by status
            status = permit.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate totals
        total_permits = len(permits)
        total_cost = sum(p.estimated_cost for p in permits if p.estimated_cost)

        return {
            "total_permits": total_permits,
            "total_estimated_cost": total_cost,
            "permit_types": type_counts,
            "permit_statuses": status_counts,
            "average_cost": total_cost / total_permits if total_permits > 0 else 0,
            "collection_date": datetime.now().isoformat()
        }


@timed_flow
@with_run_context
def collect_permits(
    cities_states: List[tuple[str, str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    permit_types: Optional[List[str]] = None,
    as_of: str = None
) -> dict:
    """Collect permits from various city/state portals.

    Args:
        cities_states: List of (city, state) tuples to collect from
        start_date: Start date for collection (default: 3 years ago)
        end_date: End date for collection (default: today)
        permit_types: Optional list of permit types to filter by
        as_of: As-of date for partitioning (YYYY-MM format)

    Returns:
        Dictionary with collection results and statistics
    """
    if as_of is None:
        as_of = datetime.now().strftime("%Y-%m")

    if cities_states is None:
        # Default to NYC and LA for demonstration
        cities_states = [("New York", "NY"), ("Los Angeles", "CA")]

    flow = PermitCollectionFlow()

    # Log flow start
    flow.log_start(cities=cities_states, start_date=start_date, end_date=end_date, as_of=as_of)

    all_permits = []
    collection_errors = []

    try:
        # Collect permits from each city/state
        for city, state in cities_states:
            try:
                city_permits = flow.fetch_permits_for_city(
                    city, state, start_date, end_date, permit_types
                )
                all_permits.extend(city_permits)
            except Exception as e:
                collection_errors.append(f"Failed to collect from {city}, {state}: {e}")
                flow.logger.error(f"Failed to collect permits from {city}, {state}: {e}")

        # Validate collected data
        if all_permits:
            flow.validate_permit_data(all_permits)

            # Store in data lake
            storage_path = flow.store_permit_data(all_permits, as_of)

            # Aggregate statistics
            statistics = flow.aggregate_permit_statistics(all_permits)
        else:
            storage_path = None
            statistics = {}

        flow.log_complete(
            0.0,
            total_permits=len(all_permits),
            cities_processed=len(cities_states),
            cities_with_errors=len(collection_errors),
            as_of=as_of
        )

        return {
            "permits_collected": len(all_permits),
            "cities_processed": len(cities_states),
            "cities_with_errors": len(collection_errors),
            "collection_errors": collection_errors,
            "storage_path": storage_path,
            "statistics": statistics,
            "as_of": as_of
        }

    except Exception as e:
        flow.log_error(str(e), 0.0, as_of=as_of)
        raise


if __name__ == "__main__":
    # For local testing
    import sys

    # Example: collect permits for NYC and LA
    result = collect_permits(
        cities_states=[("New York", "NY"), ("Los Angeles", "CA")],
        start_date=datetime.now().date(),  # Today for testing
        end_date=datetime.now().date(),   # Today for testing
        permit_types=["residential_new", "residential_renovation"]
    )
    print(f"Permit collection completed: {result}")
