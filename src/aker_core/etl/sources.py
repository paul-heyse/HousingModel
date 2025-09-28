"""Source inventory metadata for boundary and geocoding integrations.

The OpenSpec change *add-boundary-geocoding-integration* requires a clear
inventory of credentials, rate limits, and staging datasets so ETL planners can
sequence Prefect deployments without repeatedly parsing `sources_supplement.yml`.
This module keeps that information close to the ETL code while remaining
lightweight enough for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class SourceInventory:
    """Summarised metadata for an external data source."""

    id: str
    name: str
    cadence: str
    staging_datasets: Tuple[str, ...]
    requires_api_key: bool = False
    api_key_env: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    burst_size: Optional[int] = None
    default_ttl: str = "30d"
    notes: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        """Serialise the inventory entry for reporting or docs generation."""

        payload: Dict[str, object] = {
            "id": self.id,
            "name": self.name,
            "cadence": self.cadence,
            "staging_datasets": list(self.staging_datasets),
            "requires_api_key": self.requires_api_key,
            "default_ttl": self.default_ttl,
        }

        if self.api_key_env:
            payload["api_key_env"] = self.api_key_env
        if self.rate_limit_per_minute is not None:
            payload["rate_limit_per_minute"] = self.rate_limit_per_minute
        if self.burst_size is not None:
            payload["burst_size"] = self.burst_size
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload


BOUNDARY_SOURCES: Mapping[str, SourceInventory] = {
    "census_tigerweb": SourceInventory(
        id="census_tigerweb",
        name="US Census TIGERweb",
        cadence="annual",
        staging_datasets=(
            "boundaries_state",
            "boundaries_county",
            "boundaries_tract",
            "boundaries_place",
            "boundaries_zcta",
        ),
        default_ttl="365d",
        notes=(
            "ArcGIS FeatureService – respect fair-use guidance",
            "Layers exposed through load_tigerweb() helper",
        ),
    ),
    "openaddresses": SourceInventory(
        id="openaddresses",
        name="OpenAddresses",
        cadence="irregular",
        staging_datasets=("addresses",),
        default_ttl="90d",
        notes=(
            "Batch jobs produce zipped CSVs; deduplicate on hash + latitude",
            "Optional enrichment feed for amenity ROI & asset fit",
        ),
    ),
    "microsoft_buildings": SourceInventory(
        id="microsoft_buildings",
        name="Microsoft Global Building Footprints",
        cadence="irregular",
        staging_datasets=("building_footprints",),
        default_ttl="180d",
        notes=(
            "Large GeoJSON blobs – ingest per country code",
            "Topology validation required before downstream usage",
        ),
    ),
}


GEOCODER_SOURCES: Mapping[str, SourceInventory] = {
    "census_geocoder": SourceInventory(
        id="census_geocoder",
        name="US Census Geocoder",
        cadence="on_demand",
        staging_datasets=("geocode_census",),
        default_ttl="30d",
        rate_limit_per_minute=600,  # documented soft limit via Census support threads
        burst_size=30,
        notes=(
            "Supports single-line, batch, and reverse lookups",
            "Cache results to avoid repeated benchmark hits",
        ),
    ),
    "osm_nominatim": SourceInventory(
        id="osm_nominatim",
        name="OSM Nominatim",
        cadence="on_demand",
        staging_datasets=("geocode_osm",),
        default_ttl="7d",
        rate_limit_per_minute=60,  # 1 request per second recommended
        burst_size=5,
        notes=(
            "Public instance enforces user-agent/email identification",
            "Prefer self-hosted deployment for heavy workloads",
        ),
    ),
    "mapbox_geocoding": SourceInventory(
        id="mapbox_geocoding",
        name="Mapbox Geocoding API",
        cadence="on_demand",
        staging_datasets=("geocode_mapbox",),
        requires_api_key=True,
        api_key_env="AKER_MAPBOX_ACCESS_TOKEN",
        default_ttl="14d",
        rate_limit_per_minute=600,
        burst_size=60,
        notes=(
            "Commercial tier limits vary – defaults based on starter plan",
            "Forward & reverse endpoints exposed via MapboxGeocoder",
        ),
    ),
}


def get_boundary_sources() -> Iterable[SourceInventory]:
    """Return iterable over configured boundary sources."""

    return BOUNDARY_SOURCES.values()


def get_geocoder_sources() -> Iterable[SourceInventory]:
    """Return iterable over configured geocoder sources."""

    return GEOCODER_SOURCES.values()


__all__ = [
    "SourceInventory",
    "BOUNDARY_SOURCES",
    "GEOCODER_SOURCES",
    "get_boundary_sources",
    "get_geocoder_sources",
]
