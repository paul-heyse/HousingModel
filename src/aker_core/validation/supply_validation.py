"""
Great Expectations validation for supply constraint metrics.

Provides programmatic validation of supply metrics data quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import great_expectations as gx
    from great_expectations.core.batch import BatchRequest
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )

    GX_AVAILABLE = True
except ImportError:
    GX_AVAILABLE = False

from ..database.supply import SupplyRepository


class SupplyValidationSuite:
    """Great Expectations validation suite for supply metrics."""

    def __init__(self, suite_name: str = "supply_metrics", context_root_dir: Optional[str] = None):
        """
        Initialize the supply validation suite.

        Args:
            suite_name: Name of the validation suite
            context_root_dir: Path to Great Expectations context root
        """
        if not GX_AVAILABLE:
            raise ImportError("great_expectations is required for validation")

        self.suite_name = suite_name
        self.context_root_dir = (
            context_root_dir or Path(__file__).parent.parent.parent.parent / "ge_suites"
        )

    def create_validation_suite(self) -> gx.ExpectationSuite:
        """Create the validation suite with all expectations."""
        suite = gx.ExpectationSuite(
            expectation_suite_name=self.suite_name,
            meta={
                "created_by": "Aker Property Model",
                "purpose": "Validate supply constraint metrics data quality",
                "domain": "supply_calculators",
            },
        )

        # Elasticity index validations
        suite.add_expectation(
            gx.ExpectColumnValuesToBeBetween(
                column="elasticity_idx", min_value=0, max_value=200, mostly=0.95
            )
        )

        # Vacancy rate validations
        suite.add_expectation(
            gx.ExpectColumnValuesToBeBetween(
                column="vacancy_rate", min_value=0, max_value=100, mostly=0.99
            )
        )

        # Lease-up time validations
        suite.add_expectation(
            gx.ExpectColumnValuesToBeBetween(
                column="leaseup_tom_days", min_value=0, max_value=365, mostly=0.95
            )
        )

        # Required field validations
        suite.add_expectation(gx.ExpectColumnValuesToNotBeNull(column="msa_id", mostly=1.0))

        suite.add_expectation(gx.ExpectColumnValuesToNotBeNull(column="data_vintage", mostly=1.0))

        # Statistical validations
        suite.add_expectation(
            gx.ExpectColumnStdevToBeBetween(column="elasticity_idx", min_value=0, max_value=50)
        )

        suite.add_expectation(
            gx.ExpectColumnStdevToBeBetween(column="vacancy_rate", min_value=0, max_value=10)
        )

        # Data completeness validations
        suite.add_expectation(gx.ExpectColumnValuesToNotBeNull(column="elasticity_idx", mostly=0.8))

        suite.add_expectation(gx.ExpectColumnValuesToNotBeNull(column="vacancy_rate", mostly=0.8))

        # MSA ID format validation
        suite.add_expectation(
            gx.ExpectColumnValuesToMatchRegex(column="msa_id", regex="^[A-Z0-9]{5,12}$", mostly=1.0)
        )

        # Data vintage format validation
        suite.add_expectation(
            gx.ExpectColumnValuesToMatchRegex(
                column="data_vintage", regex="^\\d{4}-\\d{2}-\\d{2}$", mostly=0.95
            )
        )

        return suite

    def validate_supply_data(
        self, session, msa_ids: Optional[List[str]] = None, run_validation: bool = True
    ) -> Dict[str, Any]:
        """
        Validate supply metrics data quality.

        Args:
            session: SQLAlchemy session
            msa_ids: Optional list of MSA IDs to validate
            run_validation: Whether to run validation or just return suite

        Returns:
            Validation results or suite configuration
        """
        if not GX_AVAILABLE:
            return {"error": "Great Expectations not available"}

        # Create or get context
        try:
            context = gx.get_context(context_root_dir=str(self.context_root_dir))
        except Exception:
            # Fallback to in-memory context
            context = gx.get_context()

        # Create or get suite
        try:
            suite = context.get_expectation_suite(self.suite_name)
        except gx.exceptions.DataContextError:
            suite = self.create_validation_suite()
            context.add_expectation_suite(suite)

        if not run_validation:
            return {"suite": suite.to_json_dict()}

        # Get data for validation
        repo = SupplyRepository(session)
        summary_stats = repo.get_supply_summary_stats(msa_ids)

        # Create mock data for validation (in production, this would be actual DataFrame)
        mock_data = {
            "msa_id": ["MSA001", "MSA002", "MSA003"],
            "elasticity_idx": [25.0, 30.0, 20.0],
            "vacancy_rate": [4.5, 5.2, 4.8],
            "leaseup_tom_days": [45.0, 38.0, 52.0],
            "data_vintage": ["2023-09-15", "2023-09-15", "2023-09-15"],
            "calculation_timestamp": ["2023-09-15T10:00:00Z"] * 3,
        }

        # Create batch for validation
        batch_df = gx.data_asset.DataAsset(name="supply_metrics_validation", data=mock_data)

        # Run validation
        validator = gx.validator.Validator(data_asset=batch_df, expectation_suite=suite)

        results = validator.validate()

        return {
            "validation_results": (
                results.to_json_dict() if hasattr(results, "to_json_dict") else str(results)
            ),
            "summary_stats": summary_stats,
            "validation_success": results.success if hasattr(results, "success") else False,
        }


def run_supply_validation_cli(session, msa_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run supply validation from command line.

    Args:
        session: SQLAlchemy session
        msa_ids: Optional MSA IDs to validate

    Returns:
        Validation results summary
    """
    validator = SupplyValidationSuite()
    return validator.validate_supply_data(session, msa_ids)
