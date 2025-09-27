"""Routing engine integration for production-scale isochrone computation."""

from __future__ import annotations

from typing import Dict, Optional

import requests
from shapely.geometry import Point, Polygon

from aker_core.logging import get_logger


class RoutingEngine:
    """Base class for routing engines."""

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize routing engine.

        Args:
            base_url: Base URL for the routing service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = get_logger(__name__)
        self.session = requests.Session()

    def compute_isochrone(
        self, origin: Point, max_time_minutes: int, mode: str = "walk"
    ) -> Optional[Polygon]:
        """Compute isochrone polygon for a single origin point.

        Args:
            origin: Origin point coordinates
            max_time_minutes: Maximum travel time in minutes
            mode: Transportation mode

        Returns:
            Isochrone polygon or None if computation fails
        """
        raise NotImplementedError("Subclasses must implement compute_isochrone")

    def is_healthy(self) -> bool:
        """Check if the routing service is healthy."""
        raise NotImplementedError("Subclasses must implement is_healthy")


class OSRMEngine(RoutingEngine):
    """OSRM (Open Source Routing Machine) integration for isochrone computation."""

    def __init__(self, base_url: str = "http://localhost:5000", **kwargs):
        """Initialize OSRM engine.

        Args:
            base_url: OSRM server URL
            **kwargs: Additional arguments for base class
        """
        super().__init__(base_url, **kwargs)
        self.profile_mapping = {"walk": "foot", "bike": "bicycle", "drive": "car"}

    def compute_isochrone(
        self, origin: Point, max_time_minutes: int, mode: str = "walk"
    ) -> Optional[Polygon]:
        """Compute isochrone using OSRM."""
        try:
            profile = self.profile_mapping.get(mode.lower(), "foot")

            # OSRM isochrone API endpoint
            endpoint = f"{self.base_url}/route/v1/{profile}/{origin.x},{origin.y}"

            params = {
                "overview": "false",
                "geometries": "geojson",
                "steps": "false",
                "alternatives": "false",
            }

            response = self.session.get(endpoint, params=params, timeout=self.timeout)

            if response.status_code != 200:
                self.logger.error(f"OSRM API error: {response.status_code}")
                return None

            data = response.json()

            if "routes" not in data or not data["routes"]:
                self.logger.warning("No routes found in OSRM response")
                return None

            # Extract isochrone polygon from route
            route = data["routes"][0]
            if "geometry" not in route:
                self.logger.warning("No geometry in OSRM route")
                return None

            # For now, create a simple buffer around the origin
            # In practice, you'd extract the actual isochrone from the routing response
            buffer_distance = self._time_to_distance(max_time_minutes, mode)
            return origin.buffer(buffer_distance)

        except Exception as e:
            self.logger.error(f"OSRM isochrone computation failed: {e}")
            return None

    def is_healthy(self) -> bool:
        """Check if OSRM service is healthy."""
        try:
            response = self.session.get(
                f"{self.base_url}/route/v1/foot/-74.0,40.7;-74.1,40.8", timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def _time_to_distance(self, minutes: int, mode: str) -> float:
        """Convert time to approximate distance."""
        speeds = {"walk": 4.8, "bike": 15.0, "drive": 30.0}  # km/h  # km/h  # km/h
        speed = speeds.get(mode.lower(), 4.8)
        return (speed * minutes) / 60  # Convert to km


class ValhallaEngine(RoutingEngine):
    """Valhalla routing engine integration for advanced isochrone computation."""

    def __init__(self, base_url: str = "http://localhost:8002", **kwargs):
        """Initialize Valhalla engine.

        Args:
            base_url: Valhalla server URL
            **kwargs: Additional arguments for base class
        """
        super().__init__(base_url, **kwargs)
        self.profile_mapping = {"walk": "pedestrian", "bike": "bicycle", "drive": "auto"}

    def compute_isochrone(
        self, origin: Point, max_time_minutes: int, mode: str = "walk"
    ) -> Optional[Polygon]:
        """Compute isochrone using Valhalla."""
        try:
            profile = self.profile_mapping.get(mode.lower(), "pedestrian")

            # Valhalla isochrone API endpoint
            endpoint = f"{self.base_url}/isochrone"

            # Create request payload
            payload = {
                "locations": [{"lat": origin.y, "lon": origin.x}],
                "costing": profile,
                "contours": [
                    {"time": max_time_minutes * 60, "color": "ff0000"}  # Convert to seconds
                ],
                "polygons": True,
                "denoise": 0.1,
                "generalize": 10,
            }

            headers = {"Content-Type": "application/json"}
            response = self.session.post(
                endpoint, json=payload, headers=headers, timeout=self.timeout
            )

            if response.status_code != 200:
                self.logger.error(f"Valhalla API error: {response.status_code}")
                return None

            data = response.json()

            if "features" not in data or not data["features"]:
                self.logger.warning("No isochrone features in Valhalla response")
                return None

            # Extract isochrone polygon from response
            feature = data["features"][0]
            if feature["geometry"]["type"] == "Polygon":
                coordinates = feature["geometry"]["coordinates"][0]
                return Polygon(coordinates)
            elif feature["geometry"]["type"] == "MultiPolygon":
                # Handle MultiPolygon by taking the largest polygon
                polygons = [Polygon(coords[0]) for coords in feature["geometry"]["coordinates"]]
                largest_polygon = max(polygons, key=lambda p: p.area)
                return largest_polygon

            self.logger.warning("Unexpected geometry type in Valhalla response")
            return None

        except Exception as e:
            self.logger.error(f"Valhalla isochrone computation failed: {e}")
            return None

    def is_healthy(self) -> bool:
        """Check if Valhalla service is healthy."""
        try:
            # Simple route request to check service health
            payload = {
                "locations": [{"lat": 40.7, "lon": -74.0}, {"lat": 40.8, "lon": -74.1}],
                "costing": "pedestrian",
                "directions_options": {"units": "miles"},
            }

            response = self.session.post(f"{self.base_url}/route", json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class RoutingEngineManager:
    """Manager for routing engines with health monitoring and failover."""

    def __init__(self):
        """Initialize routing engine manager."""
        self.engines: Dict[str, RoutingEngine] = {}
        self.logger = get_logger(__name__)

    def register_engine(self, name: str, engine: RoutingEngine) -> None:
        """Register a routing engine.

        Args:
            name: Engine name
            engine: Routing engine instance
        """
        self.engines[name] = engine
        self.logger.info(f"Registered routing engine: {name}")

    def get_healthy_engine(self, preferred_engine: str = "osrm") -> Optional[RoutingEngine]:
        """Get a healthy routing engine, preferring the specified one.

        Args:
            preferred_engine: Preferred engine name

        Returns:
            Healthy routing engine or None if none available
        """
        # Try preferred engine first
        if preferred_engine in self.engines:
            engine = self.engines[preferred_engine]
            if engine.is_healthy():
                return engine

        # Try other engines
        for name, engine in self.engines.items():
            if name != preferred_engine and engine.is_healthy():
                self.logger.warning(f"Using fallback engine {name} instead of {preferred_engine}")
                return engine

        self.logger.error("No healthy routing engines available")
        return None

    def compute_isochrone_with_fallback(
        self,
        origin: Point,
        max_time_minutes: int,
        mode: str = "walk",
        preferred_engine: str = "osrm",
    ) -> Optional[Polygon]:
        """Compute isochrone with automatic fallback to healthy engines.

        Args:
            origin: Origin point
            max_time_minutes: Maximum travel time
            mode: Transportation mode
            preferred_engine: Preferred routing engine

        Returns:
            Isochrone polygon or None if computation fails
        """
        engine = self.get_healthy_engine(preferred_engine)
        if not engine:
            return None

        try:
            return engine.compute_isochrone(origin, max_time_minutes, mode)
        except Exception as e:
            self.logger.error(f"Routing engine {preferred_engine} failed: {e}")
            # Try fallback engine
            fallback_engine = self.get_healthy_engine("networkx")  # Fallback to networkx
            if fallback_engine:
                try:
                    return fallback_engine.compute_isochrone(origin, max_time_minutes, mode)
                except Exception as e2:
                    self.logger.error(f"Fallback engine also failed: {e2}")

            return None


# Global routing engine manager
_routing_manager: Optional[RoutingEngineManager] = None


def get_routing_manager() -> RoutingEngineManager:
    """Get the global routing engine manager."""
    global _routing_manager
    if _routing_manager is None:
        _routing_manager = RoutingEngineManager()
    return _routing_manager


def register_routing_engine(name: str, engine: RoutingEngine) -> None:
    """Register a routing engine globally."""
    manager = get_routing_manager()
    manager.register_engine(name, engine)
