"""Geocoding connectors with caching, rate limiting, and lineage capture."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import requests

from aker_core.cache import Cache, RateLimiter, get_cache
from aker_core.config import get_settings
from aker_core.logging import get_logger
from aker_data.lake import DataLake

logger = logging.getLogger(__name__)

CENSUS_GEOCODER_BASE_URL = "https://geocoding.geo.census.gov/geocoder"
MAPBOX_GEOCODER_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"

DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class GeocodeResult:
    """Normalised geocode response suitable for downstream modules."""

    latitude: Optional[float]
    longitude: Optional[float]
    confidence: float
    provider: str
    raw: Dict[str, Any]

    def as_record(self, *, address: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "confidence": self.confidence,
            "provider": self.provider,
            "raw": self.raw,
        }
        if address is not None:
            payload["address_input"] = address
        return payload


class BaseGeocoderConnector:
    """Shared functionality for geocoding providers."""

    def __init__(
        self,
        name: str,
        base_url: str,
        *,
        cache: Optional[Cache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        ttl: str = "7d",
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.cache = cache or get_cache()
        self.ttl = ttl
        self.rate_limiter = rate_limiter or RateLimiter(
            f"geocoder:{name}", requests_per_minute=120, burst_size=30
        )
        self.session = requests.Session()
        self.session.headers.setdefault("User-Agent", f"aker-core-geocoder/{name}")
        self.logger = get_logger(f"etl.geocoding.{name}")

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        ttl: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        request = requests.Request(method=method.upper(), url=url, params=params, headers=headers)
        prepared = request.prepare()

        cache_key = f"{self.name}:{prepared.url}"
        self.rate_limiter._wait_for_token()

        if method.upper() == "GET" and data is None:
            response = self.cache.fetch(
                prepared.url,
                etl_key=f"geocoding/{cache_key}",
                ttl=ttl or self.ttl,
                headers=prepared.headers,
            )
            return response

        # For POST/PUT or bodies, fall back to cached session directly
        expire_after = self.cache._parse_ttl(ttl or self.ttl)  # type: ignore[attr-defined]
        response = self.cache.session.request(
            method=method.upper(),
            url=url,
            params=params,
            data=data,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
            expire_after=expire_after,
        )
        response.raise_for_status()
        return response

    def _store_results(
        self,
        records: Iterable[Dict[str, Any]],
        *,
        lake: Optional[DataLake],
        dataset: str,
        as_of: Optional[str] = None,
    ) -> None:
        if lake is None:
            return
        frame = pd.DataFrame(list(records))
        if frame.empty:
            return
        frame["provider"] = self.name
        frame["as_of"] = as_of or datetime.now(UTC).strftime("%Y-%m")
        frame["ingested_at"] = datetime.now(UTC)
        lake.write(frame, dataset=dataset, as_of=frame["as_of"].iloc[0], dataset_type="geocoding")


class CensusGeocoder(BaseGeocoderConnector):
    """API client for the US Census Geocoder."""

    def __init__(
        self,
        *,
        cache: Optional[Cache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        base_url: str = CENSUS_GEOCODER_BASE_URL,
    ) -> None:
        super().__init__(
            name="census",
            base_url=base_url,
            cache=cache,
            rate_limiter=rate_limiter,
            ttl="30d",
        )

    def forward(
        self,
        address: str,
        *,
        benchmark: str = "Public_AR_Current",
        lake: Optional[DataLake] = None,
    ) -> GeocodeResult:
        params = {
            "address": address,
            "benchmark": benchmark,
            "format": "json",
        }
        response = self._request("GET", "/locations/onelineaddress", params=params)
        payload = response.json()
        match = _extract_first(payload.get("result", {}).get("addressMatches", []))
        result = _normalise_census_match(match)
        if lake is not None:
            self._store_results([
                {"address": address, **result.as_record(address=address)}
            ], lake=lake, dataset="geocode_census")
        return result

    def reverse(
        self,
        *,
        latitude: float,
        longitude: float,
        benchmark: str = "Public_AR_Current",
        lake: Optional[DataLake] = None,
    ) -> GeocodeResult:
        params = {
            "x": longitude,
            "y": latitude,
            "benchmark": benchmark,
            "format": "json",
        }
        response = self._request("GET", "/locations/coordinates", params=params)
        payload = response.json()
        match = _extract_first(payload.get("result", {}).get("addressMatches", []))
        result = _normalise_census_match(match)
        if lake is not None:
            self._store_results(
                [
                    {
                        "latitude": latitude,
                        "longitude": longitude,
                        **result.as_record(address=None),
                    }
                ],
                lake=lake,
                dataset="geocode_census",
            )
        return result

    def batch(
        self,
        rows: Sequence[Dict[str, Any]],
        *,
        benchmark: str = "Public_AR_Current",
        vintage: str = "Current_Census",
        lake: Optional[DataLake] = None,
    ) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=["id", "address", "latitude", "longitude", "confidence", "provider"])

        request_payload = {
            "benchmark": benchmark,
            "vintage": vintage,
            "addressFile": json.dumps({"records": rows}),
            "format": "json",
        }
        response = self._request(
            "POST",
            "/geographies/addressesbatch",
            data=request_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        payload = response.json()
        matches = payload.get("result", {}).get("addressMatches", [])

        records: List[Dict[str, Any]] = []
        for match in matches:
            result = _normalise_census_match(match)
            records.append(
                {
                    "id": match.get("id"),
                    "address": match.get("address") or match.get("matchedAddress"),
                    **result.as_record(),
                }
            )

        frame = pd.DataFrame(records)
        if lake is not None and not frame.empty:
            self._store_results(frame.to_dict("records"), lake=lake, dataset="geocode_census")
        return frame


class MapboxGeocoder(BaseGeocoderConnector):
    """Wrapper around Mapbox Geocoding API with optional caching."""

    def __init__(
        self,
        *,
        access_token: Optional[str] = None,
        cache: Optional[Cache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        base_url: str = MAPBOX_GEOCODER_BASE_URL,
    ) -> None:
        super().__init__(
            name="mapbox",
            base_url=base_url,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter("geocoder:mapbox", requests_per_minute=600, burst_size=60),
            ttl="14d",
        )
        settings = _safe_settings()
        self.access_token = access_token or (
            settings.mapbox_access_token.get_secret_value() if getattr(settings, "mapbox_access_token", None) else None
        )
        if not self.access_token:
            logger.warning("mapbox_token_missing", extra={"provider": "mapbox"})

    def forward(
        self,
        query: str,
        *,
        proximity: Optional[Tuple[float, float]] = None,
        limit: int = 5,
        types: str = "address,poi",
        lake: Optional[DataLake] = None,
    ) -> List[GeocodeResult]:
        if not self.access_token:
            raise RuntimeError("Mapbox access token is required for forward geocoding")
        params = {
            "access_token": self.access_token,
            "limit": limit,
            "types": types,
        }
        if proximity:
            params["proximity"] = f"{proximity[1]},{proximity[0]}"
        endpoint = f"/{requests.utils.quote(query)}.json"
        response = self._request("GET", endpoint, params=params)
        payload = response.json()
        features = payload.get("features", [])
        results = [_normalise_mapbox_feature(feature) for feature in features]
        if lake is not None and results:
            records = [result.as_record(address=query) for result in results]
            self._store_results(records, lake=lake, dataset="geocode_mapbox")
        return results

    def reverse(
        self,
        *,
        latitude: float,
        longitude: float,
        limit: int = 5,
        lake: Optional[DataLake] = None,
    ) -> List[GeocodeResult]:
        if not self.access_token:
            raise RuntimeError("Mapbox access token is required for reverse geocoding")
        endpoint = f"/{longitude},{latitude}.json"
        params = {"access_token": self.access_token, "limit": limit}
        response = self._request("GET", endpoint, params=params)
        payload = response.json()
        features = payload.get("features", [])
        results = [_normalise_mapbox_feature(feature) for feature in features]
        if lake is not None and results:
            records = [result.as_record() for result in results]
            self._store_results(records, lake=lake, dataset="geocode_mapbox")
        return results


class NominatimGeocoder(BaseGeocoderConnector):
    """Wrapper around the public OSM Nominatim endpoint."""

    def __init__(
        self,
        *,
        contact_email: Optional[str] = None,
        cache: Optional[Cache] = None,
        rate_limiter: Optional[RateLimiter] = None,
        base_url: str = NOMINATIM_BASE_URL,
    ) -> None:
        super().__init__(
            name="osm_nominatim",
            base_url=base_url,
            cache=cache,
            rate_limiter=rate_limiter or RateLimiter("geocoder:nominatim", requests_per_minute=60, burst_size=5),
            ttl="7d",
        )
        settings = _safe_settings()
        self.contact_email = contact_email or getattr(settings, "nominatim_contact_email", None)
        if self.contact_email:
            self.session.headers["From"] = self.contact_email

    def forward(
        self,
        query: str,
        *,
        limit: int = 5,
        lake: Optional[DataLake] = None,
    ) -> List[GeocodeResult]:
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
            "addressdetails": 1,
            "email": self.contact_email,
        }
        response = self._request("GET", "/search", params=params)
        payload = response.json()
        results = [_normalise_nominatim_feature(feature) for feature in payload]
        if lake is not None and results:
            records = [result.as_record(address=query) for result in results]
            self._store_results(records, lake=lake, dataset="geocode_osm")
        return results

    def reverse(
        self,
        *,
        latitude: float,
        longitude: float,
        lake: Optional[DataLake] = None,
    ) -> GeocodeResult:
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18,
            "email": self.contact_email,
        }
        response = self._request("GET", "/reverse", params=params)
        payload = response.json()
        result = _normalise_nominatim_feature(payload)
        if lake is not None:
            self._store_results([
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    **result.as_record(),
                }
            ], lake=lake, dataset="geocode_osm")
        return result


def warm_geocoding_cache(
    *,
    census: Optional[CensusGeocoder] = None,
    addresses: Sequence[str] = (),
    lake: Optional[DataLake] = None,
) -> Dict[str, int]:
    """Pre-fetch common addresses to seed the shared cache."""

    census = census or CensusGeocoder()
    processed = 0
    for address in addresses:
        try:
            census.forward(address, lake=lake)
            processed += 1
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("geocode_cache_warm_failed", extra={"address": address, "error": str(exc)})
    return {"census": processed}


def _extract_first(sequence: Sequence[Any]) -> Optional[Any]:
    return sequence[0] if sequence else None


def _normalise_census_match(match: Optional[Dict[str, Any]]) -> GeocodeResult:
    if not match:
        return GeocodeResult(latitude=None, longitude=None, confidence=0.0, provider="census", raw={})

    coordinates = match.get("coordinates") or {}
    latitude = coordinates.get("y")
    longitude = coordinates.get("x")
    side = (match.get("tigerLine") or {}).get("side")
    score = 0.9 if side else 0.7

    return GeocodeResult(
        latitude=_safe_float(latitude),
        longitude=_safe_float(longitude),
        confidence=score,
        provider="census",
        raw=match,
    )


def _normalise_mapbox_feature(feature: Dict[str, Any]) -> GeocodeResult:
    center = feature.get("center", [None, None])
    relevance = float(feature.get("relevance", 0.0))
    return GeocodeResult(
        latitude=_safe_float(center[1]),
        longitude=_safe_float(center[0]),
        confidence=min(max(relevance, 0.0), 1.0),
        provider="mapbox",
        raw=feature,
    )


def _normalise_nominatim_feature(feature: Dict[str, Any]) -> GeocodeResult:
    lat = _safe_float(feature.get("lat"))
    lon = _safe_float(feature.get("lon"))
    confidence = min(float(feature.get("importance", 0.5)), 1.0)
    return GeocodeResult(latitude=lat, longitude=lon, confidence=confidence, provider="osm_nominatim", raw=feature)


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_settings() -> Any:
    try:
        return get_settings()
    except Exception:  # pragma: no cover - environment fallback
        class _Placeholder:
            mapbox_access_token: Any = None
            nominatim_contact_email: Any = None

        return _Placeholder()


__all__ = [
    "GeocodeResult",
    "BaseGeocoderConnector",
    "CensusGeocoder",
    "MapboxGeocoder",
    "NominatimGeocoder",
    "warm_geocoding_cache",
]
