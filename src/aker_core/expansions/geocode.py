"""Geocoding helpers for expansion events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class GeocodeResult:
    latitude: Optional[float]
    longitude: Optional[float]
    confidence: float
    provider: str


class BaseGeocoder:
    """Interface for geocoding services."""

    def geocode(
        self, city: Optional[str], state: Optional[str], country: Optional[str]
    ) -> GeocodeResult:
        raise NotImplementedError


class StaticGeocoder(BaseGeocoder):
    """Simple dictionary-backed geocoder suitable for tests/offline usage."""

    def __init__(
        self, mapping: Optional[Dict[Tuple[str, Optional[str]], Tuple[float, float]]] = None
    ) -> None:
        self._mapping = mapping or {}

    def geocode(
        self, city: Optional[str], state: Optional[str], country: Optional[str]
    ) -> GeocodeResult:
        if not city:
            return GeocodeResult(latitude=None, longitude=None, confidence=0.0, provider="static")
        key = (city.lower(), (state or "").lower())
        coords = self._mapping.get(key)
        if coords:
            return GeocodeResult(
                latitude=coords[0], longitude=coords[1], confidence=0.9, provider="static"
            )
        return GeocodeResult(latitude=None, longitude=None, confidence=0.0, provider="static")


__all__ = ["BaseGeocoder", "StaticGeocoder", "GeocodeResult"]
