"""Prefect deployment configurations for ETL flows."""

from __future__ import annotations

from typing import Any, Dict

from prefect import deployment
from prefect.client.schemas import Schedule

from aker_core.config import get_settings

from .collect_permits import collect_permits
from .deal_rank_refresh import refresh_deal_rankings
from .refresh_amenity_benchmarks import refresh_amenity_benchmarks
from .refresh_economic_indicators import refresh_economic_indicators
from .refresh_hazard_metrics import refresh_hazard_metrics
from .refresh_housing_market import refresh_housing_market
from .refresh_market_data import refresh_market_data
from .refresh_boundaries import refresh_boundary_catalog
from .refresh_geocoding_cache import refresh_geocoding_cache
from .score_all_markets import score_all_markets

try:
    _settings = get_settings()
except Exception:  # pragma: no cover - defensive fallback
    _settings = None


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values so flows can apply their internal defaults."""
    return {key: value for key, value in params.items() if value is not None}


# Market data refresh - daily at 6 AM
market_data_refresh = deployment(
    name="market-data-refresh-daily",
    flow=refresh_market_data,
    schedule=Schedule(cron="0 6 * * *"),  # Daily at 6 AM
    parameters=_clean_params({"year": (_settings.acs_default_year if _settings else None)}),
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

# Deal rankings - daily at 5 AM
deal_rankings_refresh = deployment(
    name="deal-rankings-refresh-daily",
    flow=refresh_deal_rankings,
    schedule=Schedule(cron="0 5 * * *"),
    parameters={"limit": None},
    tags=["etl", "deal", "daily"],
    description="Daily refresh of ETL-adjusted deal scope rankings",
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

# Economic indicators (ACS/BFS/BLS/BEA/LODES)
economic_indicators_refresh = deployment(
    name="economic-indicators-refresh-monthly",
    flow=refresh_economic_indicators,
    schedule=Schedule(cron="0 4 5 * *"),  # Monthly on the 5th at 04:00
    parameters=_clean_params(
        {
            "acs_year": _settings.acs_default_year if _settings else None,
            "acs_variables": _settings.acs_default_variables if (_settings and _settings.acs_default_variables) else None,
            "acs_geo_requests": _settings.acs_default_geo_requests if (_settings and _settings.acs_default_geo_requests) else None,
            "bfs_time_expr": _settings.bfs_default_time_expr if (_settings and _settings.bfs_default_time_expr) else None,
            "bls_series_ids": _settings.bls_series_ids if (_settings and _settings.bls_series_ids) else None,
            "bls_start_year": _settings.bls_start_year if _settings else None,
            "bls_end_year": _settings.bls_end_year if _settings else None,
            "qcew_area_code": _settings.qcew_area_code if _settings else None,
            "qcew_year": _settings.qcew_year if _settings else None,
            "qcew_quarter": _settings.qcew_quarter if _settings else None,
            "lodes_state": _settings.lodes_state if _settings else None,
            "lodes_segment": _settings.lodes_segment if _settings else None,
            "lodes_part": _settings.lodes_part if _settings else None,
            "bea_dataset_name": _settings.bea_dataset_name if _settings else None,
            "bea_table_name": _settings.bea_table_name if _settings else None,
            "bea_geo_fips": _settings.bea_geo_fips if _settings else None,
            "bea_year": _settings.bea_year if _settings else None,
        }
    ),
    tags=["etl", "economic-indicators", "monthly"],
    description="Monthly refresh of ACS/BFS/BLS/BEA indicators feeding market analytics",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Manual variant
economic_indicators_refresh_manual = deployment(
    name="economic-indicators-refresh-manual",
    flow=refresh_economic_indicators,
    tags=["etl", "economic-indicators", "manual"],
    description="Manual refresh of ACS/BFS/BLS/BEA indicators",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Hazard metrics
hazard_metrics_refresh = deployment(
    name="hazard-metrics-refresh-daily",
    flow=refresh_hazard_metrics,
    schedule=Schedule(cron="30 2 * * *"),
    parameters={},
    tags=["etl", "hazard", "daily"],
    description="Daily refresh of hazard severity metrics feeding the Risk Engine",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

hazard_metrics_refresh_manual = deployment(
    name="hazard-metrics-refresh-manual",
    flow=refresh_hazard_metrics,
    tags=["etl", "hazard", "manual"],
    description="Manual refresh of hazard severity metrics",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Amenity benchmarks
amenity_benchmarks_refresh = deployment(
    name="amenity-benchmarks-refresh-weekly",
    flow=refresh_amenity_benchmarks,
    schedule=Schedule(cron="0 3 * * 1"),
    parameters={},
    tags=["etl", "amenities", "weekly"],
    description="Weekly refresh of amenity ROI benchmarks",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

amenity_benchmarks_refresh_manual = deployment(
    name="amenity-benchmarks-refresh-manual",
    flow=refresh_amenity_benchmarks,
    tags=["etl", "amenities", "manual"],
    description="Manual refresh of amenity ROI benchmarks",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Housing market datasets
housing_market_refresh = deployment(
    name="housing-market-refresh-monthly",
    flow=refresh_housing_market,
    schedule=Schedule(cron="0 1 7 * *"),
    parameters={},
    tags=["etl", "housing", "monthly"],
    description="Monthly refresh of Zillow, Redfin, and Apartment List datasets",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

housing_market_refresh_manual = deployment(
    name="housing-market-refresh-manual",
    flow=refresh_housing_market,
    tags=["etl", "housing", "manual"],
    description="Manual refresh of housing market datasets",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Boundary datasets
boundary_catalog_refresh = deployment(
    name="boundary-catalog-refresh-quarterly",
    flow=refresh_boundary_catalog,
    schedule=Schedule(cron="0 4 1 */3 *"),
    parameters={
        "state_fips": ["06", "12", "36", "48"],
        "building_countries": ["US"],
    },
    tags=["etl", "boundaries", "quarterly"],
    description="Quarterly ingestion of TIGERweb boundaries and supplemental geospatial datasets",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

boundary_catalog_refresh_manual = deployment(
    name="boundary-catalog-refresh-manual",
    flow=refresh_boundary_catalog,
    tags=["etl", "boundaries", "manual"],
    description="Manual refresh of boundary datasets",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)

# Geocoding cache warmers
geocoding_cache_warm_manual = deployment(
    name="geocoding-cache-warm-manual",
    flow=refresh_geocoding_cache,
    tags=["etl", "geocoding", "manual"],
    description="Warm shared geocoding cache (Census/Mapbox/Nominatim) on demand",
    version="1.0.0",
    work_pool_name="default-work-pool",
    work_queue_name="default",
)


if __name__ == "__main__":
    # Deploy all flows
    print("Deploying ETL flows...")

    for dep, description in [
        (market_data_refresh, "Market data refresh"),
        (market_scoring, "Market scoring"),
        (deal_rankings_refresh, "Deal rankings refresh"),
        (permit_collection, "Permit collection"),
        (economic_indicators_refresh, "Economic indicators refresh"),
        (hazard_metrics_refresh, "Hazard metrics refresh"),
        (amenity_benchmarks_refresh, "Amenity benchmarks refresh"),
        (housing_market_refresh, "Housing market refresh"),
        (boundary_catalog_refresh, "Boundary catalog refresh"),
        (geocoding_cache_warm_manual, "Geocoding cache warm manual"),
    ]:
        try:
            dep.apply()
            print(f"✓ {description} deployment created")
        except Exception as e:
            print(f"✗ Failed to deploy {description.lower()}: {e}")

    print("Deployment creation complete!")
