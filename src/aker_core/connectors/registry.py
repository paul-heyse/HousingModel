"""Connector registry for managing data source connectors."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from aker_core.logging import get_logger
from aker_core.run import RunContext

from .base import BaseConnector


class ConnectorRegistry:
    """Registry for managing data source connectors."""

    def __init__(self):
        """Initialize connector registry."""
        self.connectors: Dict[str, Type[BaseConnector]] = {}
        self.logger = get_logger(__name__)

        # Auto-register built-in connectors
        self._register_builtin_connectors()

    def _register_builtin_connectors(self):
        """Register built-in connector implementations."""
        # Census connectors
        try:
            from .census import BFSConnector, CensusACSConnector

            self.register_connector("census_acs", CensusACSConnector)
            self.register_connector("bfs", BFSConnector)
        except ImportError:
            self.logger.warning("Census connectors not available")

        # Economic connectors
        try:
            from .economic import BEAConnector, BLSConnector

            self.register_connector("bls", BLSConnector)
            self.register_connector("bea", BEAConnector)
        except ImportError:
            self.logger.warning("Economic connectors not available")

        # Geographic connectors
        try:
            from .geographic import GTFSConnector, OSMConnector

            self.register_connector("osm", OSMConnector)
            self.register_connector("gtfs", GTFSConnector)
        except ImportError:
            self.logger.warning("Geographic connectors not available")

        # Environmental connectors
        try:
            from .environmental import EPAAirNowConnector, NOAAHMSConnector, USGSDEMConnector

            self.register_connector("epa_airnow", EPAAirNowConnector)
            self.register_connector("noaa_hms", NOAAHMSConnector)
            self.register_connector("usgs_dem", USGSDEMConnector)
        except ImportError:
            self.logger.warning("Environmental connectors not available")

        # Other connectors
        try:
            from .other import FEMAConnector, LODESConnector

            self.register_connector("fema", FEMAConnector)
            self.register_connector("lodes", LODESConnector)
        except ImportError:
            self.logger.warning("Other connectors not available")

    def register_connector(self, name: str, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class.

        Args:
            name: Connector name
            connector_class: Connector class to register
        """
        self.connectors[name] = connector_class
        self.logger.info(f"Registered connector: {name}")

    def get_connector(self, name: str, run_context: Optional[RunContext] = None) -> BaseConnector:
        """Get connector instance by name.

        Args:
            name: Connector name
            run_context: Optional RunContext for lineage tracking

        Returns:
            Connector instance

        Raises:
            ValueError: If connector is not registered
        """
        if name not in self.connectors:
            available = ", ".join(self.connectors.keys())
            raise ValueError(f"Connector '{name}' not found. Available: {available}")

        connector_class = self.connectors[name]

        if connector_class.__init__ is BaseConnector.__init__:
            base_url = getattr(connector_class, "BASE_URL", "")
            return connector_class(
                name=name,
                base_url=base_url,
                run_context=run_context,
            )

        try:
            return connector_class(run_context=run_context)
        except TypeError:
            return connector_class()

    def list_connectors(self) -> List[str]:
        """List all registered connector names.

        Returns:
            List of connector names
        """
        return list(self.connectors.keys())

    def has_connector(self, name: str) -> bool:
        """Check if a connector is registered.

        Args:
            name: Connector name

        Returns:
            True if connector is registered
        """
        return name in self.connectors


# Global registry instance
_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry


def register_connector(name: str, connector_class: Type[BaseConnector]) -> None:
    """Register a connector globally."""
    registry = get_registry()
    registry.register_connector(name, connector_class)


def get_connector(name: str, run_context: Optional[RunContext] = None) -> BaseConnector:
    """Get connector instance by name."""
    registry = get_registry()
    return registry.get_connector(name, run_context)


def list_connectors() -> List[str]:
    """List all registered connector names."""
    registry = get_registry()
    return registry.list_connectors()


def has_connector(name: str) -> bool:
    """Check if a connector is registered."""
    registry = get_registry()
    return registry.has_connector(name)
