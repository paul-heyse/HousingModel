"""
Portfolio Exposure Monitoring and Concentration Analysis

Module: aker_portfolio
Purpose: Provides comprehensive portfolio exposure monitoring, concentration analysis,
         and automated alerting for housing investment portfolios
Author: Aker Property Model Team
Created: 2025-01-01
Modified: 2025-01-27

Dependencies:
    - aker_core: Core utilities and database access
    - aker_data: Database models and base classes
    - sqlalchemy: Database ORM for queries and transactions
    - pydantic: Data validation and serialization

Configuration:
    - Database connection required for all operations
    - Session management handled externally

Environment Variables:
    - AKER_DATABASE_URL: Database connection string
    - AKER_CACHE_PATH: Cache directory for performance optimization

API Reference:
    Public Functions:
        compute_exposures(positions, as_of_date=None, include_alerts=True, db_session=None) -> ExposureResult
            Main entry point for portfolio exposure analysis across multiple dimensions.

        get_exposure_history(dimension_type, dimension_value=None, days=30, db_session=None) -> list[dict]
            Retrieve historical exposure data for trend analysis.

        analyze_geographic_risks(msa_ids, db_session=None) -> dict[str, dict]
            Analyze geographic concentration risks for specific MSAs.

        create_exposure_threshold(dimension_type, threshold_pct, dimension_value=None, threshold_type="maximum", severity_level="warning", db_session=None) -> dict
            Create configurable exposure thresholds for automated alerting.

        get_active_alerts(db_session=None) -> list[dict]
            Retrieve all currently active portfolio alerts.

    Public Classes:
        PortfolioPosition
            Data model representing individual portfolio positions with asset details.

        ExposureResult
            Container for exposure calculation results across multiple dimensions.

        ExposureRequest
            Request object for exposure calculations with configuration options.

        PortfolioPositionImporter
            Utilities for importing portfolio positions from CSV/JSON/Excel files.

        PortfolioExporter
            Utilities for exporting exposure results to various formats.

        PortfolioDataValidator
            Validation utilities for imported portfolio data.

        PerformanceBenchmark
            Tools for benchmarking exposure calculation performance.

        DataBackfillUtility
            Utilities for backfilling historical exposure data.

        ExposureVisualization
            Dashboard-ready data structures for exposure visualization.

        ExposureTrendAnalyzer
            Tools for analyzing exposure trends over time.

        ExposureComparisonTool
            Utilities for comparing current exposures to limits and thresholds.

        AlertManager
            Service for managing exposure thresholds and alerts.

        PortfolioEngine
            Core engine for exposure calculations and database operations.

        GeographicExposureAnalyzer
            Specialized analysis for geographic concentration risks.

        PortfolioPositionNormalizer
            Utilities for normalizing and validating portfolio position data.

    Public Constants:
        None

Examples:
    Basic portfolio exposure analysis:

    ```python
    from aker_portfolio import compute_exposures, PortfolioPosition
    from sqlalchemy.orm import Session

    # Define portfolio positions
    positions = [
        PortfolioPosition(
            asset_id="asset_1",
            strategy="value_add",
            state="CA",
            msa_id="31080",  # Los Angeles
            position_value=1000000,
            units=50
        ),
        PortfolioPosition(
            asset_id="asset_2",
            strategy="core_plus",
            state="TX",
            msa_id="19100",  # Dallas
            position_value=1500000,
            units=75
        )
    ]

    # Calculate exposures with database session
    with Session() as session:
        result = compute_exposures(positions, db_session=session)
        print(f"Total portfolio value: ${result.total_portfolio_value}")
        print(f"Strategy exposures: {[(exp.dimension_value, exp.exposure_pct) for exp in result.exposures if exp.dimension_type == 'strategy']}")
    ```

    Geographic risk analysis:

    ```python
    from aker_portfolio import analyze_geographic_risks

    with Session() as session:
        risks = analyze_geographic_risks(["31080", "19100"], db_session=session)
        for msa_id, risk_data in risks.items():
            print(f"MSA {msa_id}: {risk_data}")
    ```

Error Handling:
    - ValueError: Raised for invalid input parameters or missing required data
    - ValidationError: Raised when position data fails validation
    - DatabaseError: Raised for database connection or query issues

Performance Notes:
    - Exposure calculations scale linearly with number of positions
    - Database operations are optimized with proper indexing
    - Caching can be implemented for frequently accessed historical data
    - Large portfolios (>1000 positions) may benefit from batch processing

Testing:
    Comprehensive test suite in tests/test_portfolio_exposure.py
    Coverage includes unit tests, integration tests, and performance benchmarks
    Mock database sessions used for isolated testing

Security:
    - All database operations require explicit session management
    - Input validation prevents injection attacks
    - No sensitive data stored in module-level variables
    - Audit logging integrated with core logging system

See Also:
    - aker_core.run: Run context and session management
    - aker_data.models: Database models and schema definitions
    - aker_gui: GUI components for portfolio visualization
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

# Database session will be passed as parameter
from .alerts import AlertManager
from .engine import PortfolioEngine
from .geographic import GeographicExposureAnalyzer
from .import_export import PortfolioDataValidator, PortfolioExporter, PortfolioPositionImporter
from .normalization import PortfolioPositionNormalizer
from .performance import DataBackfillUtility, PerformanceBenchmark
from .types import ExposureRequest, ExposureResult, PortfolioPosition
from .visualization import ExposureComparisonTool, ExposureTrendAnalyzer, ExposureVisualization


def compute_exposures(
    positions: list[PortfolioPosition],
    as_of_date: Optional[datetime] = None,
    include_alerts: bool = True,
    db_session: Optional[Session] = None,
) -> ExposureResult:
    """
    Compute portfolio exposures across multiple dimensions.

    This is the main entry point for portfolio exposure analysis.

    Args:
        positions: List of portfolio positions to analyze
        as_of_date: Date for calculation (defaults to current date)
        include_alerts: Whether to check for threshold breaches
        db_session: Database session (uses default if not provided)

    Returns:
        ExposureResult with calculated exposures and alerts

    Example:
        >>> positions = [
        ...     PortfolioPosition(
        ...         asset_id="asset_1",
        ...         strategy="value_add",
        ...         state="CA",
        ...         position_value=1000000,
        ...         units=50
        ...     )
        ... ]
        >>> result = compute_exposures(positions)
        >>> print(f"Total portfolio value: ${result.total_portfolio_value}")
    """
    if db_session is None:
        raise ValueError("Database session must be provided")

    # Normalize and validate positions
    normalizer = PortfolioPositionNormalizer()
    normalized_positions = normalizer.normalize_position_values(positions)

    validation_result = normalizer.validate_positions(normalized_positions)
    if not validation_result.is_valid:
        error_msg = "Position validation failed: " + "; ".join(validation_result.errors)
        raise ValueError(error_msg)

    # Create exposure request
    request = ExposureRequest(
        positions=normalized_positions,
        as_of_date=as_of_date,
        include_alerts=include_alerts,
    )

    # Compute exposures
    engine = PortfolioEngine(db_session)
    result = engine.compute_exposures(request)

    return result


def get_exposure_history(
    dimension_type: str,
    dimension_value: Optional[str] = None,
    days: int = 30,
    db_session: Optional[Session] = None,
) -> list[dict]:
    """
    Get historical exposure data for analysis.

    Args:
        dimension_type: Type of dimension to filter by
        dimension_value: Specific dimension value (optional)
        days: Number of days of history to retrieve
        db_session: Database session

    Returns:
        List of exposure data points
    """
    if db_session is None:
        raise ValueError("Database session must be provided")

    _ = PortfolioEngine(db_session)

    # This would query the database for historical data
    # For now, return empty list as implementation would require
    # additional database queries
    return []


def analyze_geographic_risks(
    msa_ids: list[str],
    db_session: Optional[Session] = None,
) -> dict[str, dict]:
    """
    Analyze geographic concentration risks for specific MSAs.

    Args:
        msa_ids: List of MSA IDs to analyze
        db_session: Database session

    Returns:
        Risk analysis by MSA
    """
    if db_session is None:
        raise ValueError("Database session must be provided")

    analyzer = GeographicExposureAnalyzer(db_session)
    results = {}

    for msa_id in msa_ids:
        results[msa_id] = analyzer.get_geographic_risk_factors(msa_id)

    return results


# Convenience functions for alert management
def create_exposure_threshold(
    dimension_type: str,
    threshold_pct: float,
    dimension_value: Optional[str] = None,
    threshold_type: str = "maximum",
    severity_level: str = "warning",
    db_session: Optional[Session] = None,
) -> dict:
    """Create a new exposure threshold."""
    if db_session is None:
        raise ValueError("Database session must be provided")

    alert_manager = AlertManager(db_session)
    threshold = alert_manager.create_threshold(
        dimension_type=dimension_type,
        threshold_pct=threshold_pct,
        dimension_value=dimension_value,
        threshold_type=threshold_type,
        severity_level=severity_level,
    )

    return threshold.dict()


def get_active_alerts(db_session: Optional[Session] = None) -> list[dict]:
    """Get all active portfolio alerts."""
    if db_session is None:
        raise ValueError("Database session must be provided")

    engine = PortfolioEngine(db_session)
    alerts = engine.get_active_alerts()

    return [alert.dict() for alert in alerts]


__all__ = [
    # Core functions
    "compute_exposures",
    "get_exposure_history",
    "analyze_geographic_risks",
    "create_exposure_threshold",
    "get_active_alerts",

    # Data models
    "PortfolioPosition",
    "ExposureResult",
    "ExposureRequest",

    # Utility classes
    "PortfolioPositionImporter",
    "PortfolioExporter",
    "PortfolioDataValidator",
    "PerformanceBenchmark",
    "DataBackfillUtility",
    "ExposureVisualization",
    "ExposureTrendAnalyzer",
    "ExposureComparisonTool",
    "AlertManager",
    "PortfolioEngine",
    "GeographicExposureAnalyzer",
    "PortfolioPositionNormalizer",
]
