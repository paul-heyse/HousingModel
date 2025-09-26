"""Connector registry for managing city/state-specific permit connectors."""

from __future__ import annotations

import importlib
from typing import Dict, Optional, Type

from aker_core.logging import get_logger
from aker_core.run import RunContext

from .connector import PermitsConnector


class ConnectorRegistry:
    """Registry for managing permit portal connectors by city/state."""

    def __init__(self):
        """Initialize connector registry."""
        self.connectors: Dict[str, Type[PermitsConnector]] = {}
        self.logger = get_logger(__name__)

        # Register built-in connectors
        self._register_builtin_connectors()

    def _register_builtin_connectors(self):
        """Register built-in connector implementations."""
        try:
            # Try to import and register NYC connector
            from .connectors.nyc import NYCConnector
            self.register_connector("New York", "NY", NYCConnector)
        except ImportError:
            self.logger.warning("NYC connector not available")

        try:
            # Try to import and register LA connector
            from .connectors.la import LAConnector
            self.register_connector("Los Angeles", "CA", LAConnector)
        except ImportError:
            self.logger.warning("LA connector not available")

    def register_connector(
        self,
        city: str,
        state: str,
        connector_class: Type[PermitsConnector]
    ) -> None:
        """Register a connector for a city/state combination.

        Args:
            city: City name
            state: State abbreviation
            connector_class: Connector class to register
        """
        key = self._make_key(city, state)
        self.connectors[key] = connector_class
        self.logger.info(f"Registered connector for {city}, {state}")

    def get_connector(
        self,
        city: str,
        state: str,
        run_context: Optional[RunContext] = None
    ) -> PermitsConnector:
        """Get connector for a city/state combination.

        Args:
            city: City name
            state: State abbreviation
            run_context: Optional RunContext for lineage tracking

        Returns:
            PermitsConnector instance

        Raises:
            ValueError: If no connector is registered for the city/state
        """
        key = self._make_key(city, state)

        if key not in self.connectors:
            raise ValueError(f"No connector registered for {city}, {state}")

        connector_class = self.connectors[key]
        return connector_class(city, state, run_context)

    def list_registered_connectors(self) -> list[tuple[str, str]]:
        """List all registered city/state combinations.

        Returns:
            List of (city, state) tuples
        """
        cities_states = []
        for key in self.connectors.keys():
            city, state = key.split("|", 1)
            cities_states.append((city, state))
        return cities_states

    def has_connector(self, city: str, state: str) -> bool:
        """Check if a connector is registered for a city/state.

        Args:
            city: City name
            state: State abbreviation

        Returns:
            True if connector is registered
        """
        key = self._make_key(city, state)
        return key in self.connectors

    def _make_key(self, city: str, state: str) -> str:
        """Create registry key from city and state."""
        return f"{city}|{state}"

    def register_connector_by_pattern(
        self,
        pattern: str,
        connector_class: Type[PermitsConnector]
    ) -> None:
        """Register a connector for cities matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "NYC|*")
            connector_class: Connector class to register
        """
        # For now, just register exact matches
        # In a more sophisticated implementation, this could support wildcards
        pass


# Global registry instance
_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry


def register_connector(
    city: str,
    state: str,
    connector_class: Type[PermitsConnector]
) -> None:
    """Register a connector for a city/state combination."""
    registry = get_registry()
    registry.register_connector(city, state, connector_class)


def get_connector(
    city: str,
    state: str,
    run_context: Optional[RunContext] = None
) -> PermitsConnector:
    """Get connector for a city/state combination."""
    registry = get_registry()
    return registry.get_connector(city, state, run_context)


def list_connectors() -> list[tuple[str, str]]:
    """List all registered connectors."""
    registry = get_registry()
    return registry.list_registered_connectors()


def has_connector(city: str, state: str) -> bool:
    """Check if a connector is registered for a city/state."""
    registry = get_registry()
    return registry.has_connector(city, state)
