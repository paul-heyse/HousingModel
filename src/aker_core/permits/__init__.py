"""Permit portal ingestion system with pluggable connectors."""

from .connector import PermitsConnector, get_connector
from .models import PermitRecord, PermitStatus, PermitType
from .registry import ConnectorRegistry

__all__ = [
    "PermitsConnector",
    "get_connector",
    "PermitRecord",
    "PermitStatus",
    "PermitType",
    "ConnectorRegistry",
]
