"""Prefect deployment configurations for ETL flows."""

from __future__ import annotations

from prefect import deployment
from prefect.client.schemas import Schedule

from .collect_permits import collect_permits
from .refresh_market_data import refresh_market_data
from .score_all_markets import score_all_markets

# Market data refresh - daily at 6 AM
market_data_refresh = deployment(
    name="market-data-refresh-daily",
    flow=refresh_market_data,
    schedule=Schedule(cron="0 6 * * *"),  # Daily at 6 AM
    parameters={"year": "2022"},  # Default year, can be overridden
    tags=["etl", "market-data", "daily"],
    description="Daily refresh of market data from external sources",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Market scoring - weekly on Monday at 8 AM
market_scoring = deployment(
    name="market-scoring-weekly",
    flow=score_all_markets,
    schedule=Schedule(cron="0 8 * * 1"),  # Weekly on Monday at 8 AM
    tags=["etl", "scoring", "weekly"],
    description="Weekly scoring of all markets using latest data",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Manual deployments (no schedule)
market_data_refresh_manual = deployment(
    name="market-data-refresh-manual",
    flow=refresh_market_data,
    tags=["etl", "market-data", "manual"],
    description="Manual refresh of market data",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

market_scoring_manual = deployment(
    name="market-scoring-manual",
    flow=score_all_markets,
    tags=["etl", "scoring", "manual"],
    description="Manual scoring of all markets",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Permit collection - weekly on Wednesday at 2 AM
permit_collection = deployment(
    name="permit-collection-weekly",
    flow=collect_permits,
    schedule=Schedule(cron="0 2 * * 3"),  # Weekly on Wednesday at 2 AM
    parameters={
        "cities_states": [("New York", "NY"), ("Los Angeles", "CA")],
        "permit_types": ["residential_new", "residential_renovation", "commercial_new"],
    },
    tags=["etl", "permits", "weekly"],
    description="Weekly collection of building permits from major cities",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Permit collection manual (no schedule)
permit_collection_manual = deployment(
    name="permit-collection-manual",
    flow=collect_permits,
    tags=["etl", "permits", "manual"],
    description="Manual collection of building permits",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)


if __name__ == "__main__":
    # Deploy all flows
    print("Deploying ETL flows...")

    try:
        market_data_refresh.apply()
        print("✓ Market data refresh deployment created")
    except Exception as e:
        print(f"✗ Failed to deploy market data refresh: {e}")

    try:
        market_scoring.apply()
        print("✓ Market scoring deployment created")
    except Exception as e:
        print(f"✗ Failed to deploy market scoring: {e}")

    try:
        permit_collection.apply()
        print("✓ Permit collection deployment created")
    except Exception as e:
        print(f"✗ Failed to deploy permit collection: {e}")

    print("Deployment complete!")
