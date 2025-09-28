"""Prefect flow to prime shared geocoding caches."""

from __future__ import annotations

from typing import Dict, Sequence

from aker_core.cache import get_cache
from aker_core.etl.geocoding import (
    CensusGeocoder,
    MapboxGeocoder,
    NominatimGeocoder,
    warm_geocoding_cache,
)
from aker_data.lake import DataLake

from .base import etl_task, timed_flow, with_run_context


@etl_task("warm-census-cache", "Prime Census Geocoder cache with common addresses")
@with_run_context
def warm_census_task(addresses: Sequence[str]) -> Dict[str, int]:
    census = CensusGeocoder(cache=get_cache())
    lake = DataLake()
    return warm_geocoding_cache(census=census, addresses=addresses, lake=lake)


@etl_task("warm-mapbox-cache", "Prime Mapbox geocoding cache where licensed")
@with_run_context
def warm_mapbox_task(queries: Sequence[str]) -> Dict[str, int]:
    if not queries:
        return {"mapbox": 0}
    connector = MapboxGeocoder(cache=get_cache())
    lake = DataLake()
    processed = 0
    for query in queries:
        try:
            connector.forward(query, lake=lake)
            processed += 1
        except RuntimeError:
            # Token missing – stop trying to avoid rate limit noise
            return {"mapbox": 0}
        except Exception as exc:  # pragma: no cover - defensive logging
            connector.logger.warning("mapbox_geocode_failed", query=query, error=str(exc))
    return {"mapbox": processed}


@etl_task("warm-nominatim-cache", "Prime Nominatim cache respecting fair use")
@with_run_context
def warm_nominatim_task(queries: Sequence[str]) -> Dict[str, int]:
    if not queries:
        return {"osm_nominatim": 0}
    connector = NominatimGeocoder(cache=get_cache())
    lake = DataLake()
    processed = 0
    for query in queries:
        try:
            connector.forward(query, lake=lake)
            processed += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            connector.logger.warning("nominatim_geocode_failed", query=query, error=str(exc))
    return {"osm_nominatim": processed}


@timed_flow
def refresh_geocoding_cache(
    census_addresses: Sequence[str] = (),
    mapbox_queries: Sequence[str] = (),
    nominatim_queries: Sequence[str] = (),
) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    if census_addresses:
        summary.update(warm_census_task(addresses=census_addresses))
    if mapbox_queries:
        summary.update(warm_mapbox_task(queries=mapbox_queries))
    if nominatim_queries:
        summary.update(warm_nominatim_task(queries=nominatim_queries))
    return summary


__all__ = ["refresh_geocoding_cache"]

