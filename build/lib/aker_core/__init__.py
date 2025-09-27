"""Core runtime utilities for the Aker Property Model."""

from .cache import Cache, RateLimiter, fetch, get_cache
from .config import Settings, build_run_config, get_settings, reset_settings_cache
from .plugins import available, clear, discover, get, override, register, unregister
from .ports import AssetEvaluator, DealArchetypeModel, MarketScorer, RiskEngine
from .run import RunContext, RunContextState
from .validation import (
    GreatExpectationsValidator,
    ValidationResult,
    get_validation_suites_dir,
    list_available_suites,
    load_validation_suite,
    validate_data_quality,
    validate_dataset,
)

# Import geospatial utilities
try:
    from aker_geo import to_storage, to_ui, validate_crs, validate_geometry
except ImportError:
    # Geospatial dependencies not available
    to_storage = None
    to_ui = None
    validate_geometry = None
    validate_crs = None

__all__ = [
    "Settings",
    "build_run_config",
    "get_settings",
    "reset_settings_cache",
    "RunContext",
    "RunContextState",
    "MarketScorer",
    "AssetEvaluator",
    "DealArchetypeModel",
    "RiskEngine",
    "register",
    "get",
    "discover",
    "override",
    "available",
    "unregister",
    "clear",
    "Cache",
    "RateLimiter",
    "fetch",
    "get_cache",
    "GreatExpectationsValidator",
    "ValidationResult",
    "get_validation_suites_dir",
    "list_available_suites",
    "load_validation_suite",
    "validate_data_quality",
    "validate_dataset",
    "to_storage",
    "to_ui",
    "validate_geometry",
    "validate_crs",
]
