"""Core runtime utilities for the Aker Property Model."""

from .cache import Cache, RateLimiter, fetch, get_cache
from .config import Settings, build_run_config, get_settings, reset_settings_cache
from .connectors import BaseConnector, ConnectorRegistry, DataConnector, get_connector
from .connectors.supply_data import (
    BuildingPermitData,
    CensusConnector,
    HouseholdEstimate,
    HUDConnector,
    HUDVacancyData,
    LeaseDataConnector,
    LeaseTransaction,
    PermitPortalConnector,
    SupplyDataETL,
)
from .expansions import ExpansionEvent, ExpansionsIngestor, FeedConfig, ReviewQueue
from .markets import MarketPillarScores
from .markets import score as compose_market_score
from .markets import score_many as compose_market_scores
from .plugins import available, clear, discover, get, override, register, unregister
from .ports import AssetEvaluator, DealArchetypeModel, MarketScorer, RiskEngine
from .run import RunContext, RunContextState
from .scoring import RobustNormalizationError, robust_minmax
from .supply import (
    SupplyPerformanceOptimizer,
    calculate_supply_metrics,
    elasticity,
    get_supply_scores_for_scoring,
    inverse_elasticity_score,
    inverse_leaseup_score,
    inverse_vacancy_score,
    leaseup_tom,
    optimize_supply_calculations,
    vacancy,
    validate_supply_data_quality,
)
from .validation import (
    GreatExpectationsValidator,
    ValidationResult,
    get_validation_suites_dir,
    list_available_suites,
    load_validation_suite,
    validate_data_quality,
    validate_dataset,
)

try:
    from .validation.supply_validation import SupplyValidationSuite, run_supply_validation_cli
from .integration.market_analysis import MarketAnalysisPipeline, analyze_market, analyze_multiple_markets, get_market_rankings, MarketAnalysisResult
except ModuleNotFoundError:  # pragma: no cover - optional validation component
    SupplyValidationSuite = None
    run_supply_validation_cli = None

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
    "MarketPillarScores",
    "compose_market_score",
    "compose_market_scores",
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
    "BaseConnector",
    "DataConnector",
    "ConnectorRegistry",
    "get_connector",
    "HUDConnector",
    "CensusConnector",
    "PermitPortalConnector",
    "LeaseDataConnector",
    "SupplyDataETL",
    "robust_minmax",
    "RobustNormalizationError",
    "BuildingPermitData",
    "HouseholdEstimate",
    "HUDVacancyData",
    "LeaseTransaction",
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
    "ExpansionEvent",
    "ExpansionsIngestor",
    "FeedConfig",
    "ReviewQueue",
    "elasticity",
    "inverse_elasticity_score",
    "vacancy",
    "inverse_vacancy_score",
    "leaseup_tom",
    "inverse_leaseup_score",
    "calculate_supply_metrics",
    "get_supply_scores_for_scoring",
    "validate_supply_data_quality",
    "SupplyPerformanceOptimizer",
    "optimize_supply_calculations",
    "MarketAnalysisPipeline",
    "analyze_market",
    "analyze_multiple_markets",
    "get_market_rankings",
    "MarketAnalysisResult",
]

if SupplyValidationSuite is not None and run_supply_validation_cli is not None:
    __all__.extend(["SupplyValidationSuite", "run_supply_validation_cli"])
