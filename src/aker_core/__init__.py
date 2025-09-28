"""Public entry points for the Aker Property Model core layer.

The module mirrors requirements captured in `openspec/specs/core/spec.md` by
exposing configuration, run tracking, scoring, connector, and validation
primitives.  Importers should rely on these re-exports instead of reaching into
submodules so behaviour stays aligned with documented specs.
"""

from .asset import AssetFitResult
from .asset import fit as asset_fit
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
from .exceptions import (
    AkerBaseException,
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    DataProcessingError,
    DatabaseError,
    ExternalAPIError,
    FileProcessingError,
    PerformanceError,
    ValidationError,
    business_logic_error,
    configuration_error,
    database_error,
    external_api_error,
    validation_error,
)
from .scoring import RobustNormalizationError, robust_minmax
# Governance surface is optional in lightweight deployments; we keep a clear
# runtime failure so spec-required gates cannot be bypassed silently.
try:  # pragma: no cover - optional governance stack
    from .governance import ICWorkflow, advance as advance_ic_gate
except Exception:  # pragma: no cover
    ICWorkflow = None

    def advance_ic_gate(*args, **kwargs):  # type: ignore[override]
        raise RuntimeError("IC governance components are not available in this environment")
# Excel exports are likewise optional; fallbacks keep CLI/SDK consumers aware
# when the export stack is not installed on the current worker.
try:  # pragma: no cover - optional exports stack
    from .exports import ExcelWorkbookBuilder, to_excel as generate_excel_report
except Exception:  # pragma: no cover
    ExcelWorkbookBuilder = None

    def generate_excel_report(*args, **kwargs):  # type: ignore[override]
        raise RuntimeError("Excel export components are not available in this environment")
# Supply analytics can be trimmed in minimal installs; providing explicit
# `None` placeholders keeps IDEs and runtime checks honest about availability.
try:  # pragma: no cover - optional supply stack
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
except Exception:  # pragma: no cover
    SupplyPerformanceOptimizer = None
    calculate_supply_metrics = None
    elasticity = None
    get_supply_scores_for_scoring = None
    inverse_elasticity_score = None
    inverse_leaseup_score = None
    inverse_vacancy_score = None
    leaseup_tom = None
    optimize_supply_calculations = None
    vacancy = None
    validate_supply_data_quality = None
from .utils import (
    calculate_percentage_change,
    chunk_list,
    create_timestamp,
    format_currency,
    format_percentage,
    hash_dict,
    is_valid_uuid,
    normalize_to_range,
    safe_divide,
    safe_float_conversion,
    safe_int_conversion,
    sanitize_string,
    validate_required_fields,
)
from .validation import (
    GreatExpectationsValidator,
    SchemaValidator,
    ValidationResult,
    list_available_suites,
    validate_data_quality,
    validate_dataset,
)

# Optional components
try:  # pragma: no cover
    from .integration.market_analysis import (
        MarketAnalysisPipeline,
        MarketAnalysisResult,
        analyze_market,
        analyze_multiple_markets,
        get_market_rankings,
    )
    from .validation.supply_validation import SupplyValidationSuite, run_supply_validation_cli
except ModuleNotFoundError:  # pragma: no cover - optional validation component
    SupplyValidationSuite = None
    run_supply_validation_cli = None

# Import geospatial utilities
try:  # pragma: no cover
    from aker_geo import to_storage, to_ui, validate_crs, validate_geometry
except ImportError:  # pragma: no cover
    # Geospatial dependencies not available
    to_storage = None
    to_ui = None
    validate_geometry = None
    validate_crs = None

# OPS exports
try:  # pragma: no cover
    from .database.ops import OpsRepository
    from .ops import pricing_rules, reputation_index
    from .ops.cli import main as ops_cli
except Exception:  # pragma: no cover
    reputation_index = None
    pricing_rules = None
    ops_cli = None
    OpsRepository = None

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
    "AssetFitResult",
    "asset_fit",
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
    "AkerBaseException",
    "ValidationError",
    "DatabaseError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "DataProcessingError",
    "ExternalAPIError",
    "FileProcessingError",
    "BusinessLogicError",
    "PerformanceError",
    "validation_error",
    "database_error",
    "configuration_error",
    "external_api_error",
    "business_logic_error",
    "safe_float_conversion",
    "safe_int_conversion",
    "format_currency",
    "format_percentage",
    "calculate_percentage_change",
    "hash_dict",
    "validate_required_fields",
    "sanitize_string",
    "create_timestamp",
    "is_valid_uuid",
    "chunk_list",
    "safe_divide",
    "normalize_to_range",
    "BuildingPermitData",
    "HouseholdEstimate",
    "HUDVacancyData",
    "LeaseTransaction",
    "GreatExpectationsValidator",
    "SchemaValidator",
    "ValidationResult",
    "list_available_suites",
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
    "reputation_index",
    "pricing_rules",
    "ops_cli",
    "OpsRepository",
    "ExcelWorkbookBuilder",
    "generate_excel_report",
]

if SupplyValidationSuite is not None and run_supply_validation_cli is not None:
    __all__.extend(["SupplyValidationSuite", "run_supply_validation_cli"])
