"""Great Expectations validation integration with Prefect."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from great_expectations.core.batch import BatchRequest
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.expectation_validation_result import ExpectationSuiteValidationResult
from great_expectations.data_context import FileDataContext
from prefect import task
from prefect.logging import get_logger

from aker_core.logging import get_logger as get_structlog_logger
from aker_core.run import RunContext


class ValidationResult:
    """Container for Great Expectations validation results."""

    def __init__(self, results: List[ExpectationSuiteValidationResult]):
        self.results = results
        self.success = all(result.success for result in results)
        self.failed_expectations = self._get_failed_expectations()

    def _get_failed_expectations(self) -> List[Dict[str, Any]]:
        """Extract failed expectations from validation results."""
        failed = []
        for result in self.results:
            for expectation_result in result.results:
                if not expectation_result.success:
                    failed.append({
                        "expectation_type": expectation_result.expectation_config.type,
                        "column": expectation_result.expectation_config.kwargs.get("column", "N/A"),
                        "message": str(expectation_result.result)
                    })
        return failed

    @property
    def total_expectations(self) -> int:
        """Total number of expectations evaluated."""
        return sum(len(result.results) for result in self.results)

    @property
    def successful_expectations(self) -> int:
        """Number of successful expectations."""
        return self.total_expectations - len(self.failed_expectations)

    @property
    def failure_rate(self) -> float:
        """Percentage of failed expectations."""
        return len(self.failed_expectations) / self.total_expectations if self.total_expectations > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "total_expectations": self.total_expectations,
            "successful_expectations": self.successful_expectations,
            "failed_expectations": len(self.failed_expectations),
            "failure_rate": self.failure_rate,
            "failed_details": self.failed_expectations
        }


class GreatExpectationsValidator:
    """Great Expectations validator for data quality validation."""

    def __init__(self, context_root_dir: Optional[str] = None, run_context: Optional[RunContext] = None):
        """Initialize Great Expectations validator.

        Args:
            context_root_dir: Directory for Great Expectations context (default: ./gx)
            run_context: Optional RunContext for lineage tracking
        """
        self.context_root_dir = context_root_dir or "./gx"
        self.run_context = run_context
        self.logger = get_logger(__name__)
        self.structlog_logger = get_structlog_logger(__name__)

        # Initialize or load Great Expectations context
        self.context = self._get_or_create_context()

    def _get_or_create_context(self) -> FileDataContext:
        """Get or create Great Expectations context."""
        gx_dir = Path(self.context_root_dir)

        # Create directory if it doesn't exist
        gx_dir.mkdir(parents=True, exist_ok=True)

        # Create basic great_expectations.yml if it doesn't exist
        gx_yml = gx_dir / "great_expectations.yml"
        if not gx_yml.exists():
            gx_config = {
                "config_version": 3.0,
                "datasources": {
                    "pandas": {
                        "class_name": "PandasDatasource",
                        "data_asset_type": {
                            "class_name": "PandasDataset",
                        }
                    }
                },
                "expectations_store_name": "expectations_store",
                "validations_store_name": "validations_store",
                "evaluation_parameter_store_name": "evaluation_parameter_store",
                "profiler_store_name": "profiler_store",
                "checkpoint_store_name": "checkpoint_store",
                "stores": {
                    "expectations_store": {
                        "class_name": "ExpectationsStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "expectations/"
                        }
                    },
                    "validations_store": {
                        "class_name": "ValidationsStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "validations/"
                        }
                    },
                    "evaluation_parameter_store": {
                        "class_name": "EvaluationParameterStore"
                    },
                    "profiler_store": {
                        "class_name": "ProfilerStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "profilers/"
                        }
                    },
                    "checkpoint_store": {
                        "class_name": "CheckpointStore",
                        "store_backend": {
                            "class_name": "TupleFilesystemStoreBackend",
                            "base_directory": "checkpoints/"
                        }
                    }
                }
            }
            import yaml
            with open(gx_yml, 'w') as f:
                yaml.dump(gx_config, f, default_flow_style=False)

        return FileDataContext(gx_dir)

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        suite_name: str,
        data_asset_name: str = "validation_data"
    ) -> ValidationResult:
        """Validate a DataFrame using Great Expectations suite.

        Args:
            df: DataFrame to validate
            suite_name: Name of expectation suite to use
            data_asset_name: Name for the data asset

        Returns:
            ValidationResult with success status and detailed results
        """
        try:
            # Create batch request for pandas DataFrame
            batch_request = BatchRequest(
                datasource_name="pandas",
                data_connector_name="runtime",
                data_asset_name=data_asset_name,
                runtime_parameters={"batch_data": df},
                batch_spec_passthrough={"reader_method": "read_csv"},
            )

            # Get expectation suite
            suite = self.context.get_expectation_suite(suite_name)

            # Run validation
            validator = self.context.get_validator(
                batch_request=batch_request,
                expectation_suite_name=suite_name,
            )

            results = validator.validate()

            # Log validation results
            self._log_validation_results(suite_name, results)

            # Log to lineage if available
            if self.run_context:
                self.run_context.log_data_lake_operation(
                    operation="data_validation",
                    dataset=f"validation:{suite_name}",
                    path=data_asset_name,
                    metadata={
                        "suite_name": suite_name,
                        "success": all(result.success for result in results.results),
                        "total_expectations": len(results.results) if hasattr(results, 'results') else 0,
                        "failed_expectations": len([r for r in results.results if not r.success]) if hasattr(results, 'results') else 0
                    }
                )

            return ValidationResult([results] if hasattr(results, 'results') else results.results)

        except Exception as e:
            self.logger.error(f"Validation failed for suite {suite_name}: {e}")
            self.structlog_logger.error(
                "validation_failed",
                suite_name=suite_name,
                error=str(e),
                success=False
            )

            # Return failed result
            return ValidationResult([])

    def _log_validation_results(self, suite_name: str, results: Any):
        """Log validation results to both Prefect and structured logs."""
        if hasattr(results, 'results') and results.results:
            total = len(results.results)
            failed = len([r for r in results.results if not r.success])
            success = all(r.success for r in results.results)

            self.logger.info(
                f"Validation {suite_name}: {total - failed}/{total} expectations passed"
            )

            self.structlog_logger.info(
                "validation_completed",
                suite_name=suite_name,
                success=success,
                total_expectations=total,
                failed_expectations=failed
            )

            # Log individual failures
            for result in results.results:
                if not result.success:
                    self.logger.warning(
                        f"Failed expectation: {result.expectation_config.type}"
                    )
        else:
            self.logger.warning(f"Validation {suite_name}: No results available")

    def create_suite_from_yaml(self, yaml_path: str, suite_name: Optional[str] = None) -> str:
        """Create expectation suite from YAML file.

        Args:
            yaml_path: Path to YAML suite file
            suite_name: Optional name for the suite (defaults to filename)

        Returns:
            Name of created suite
        """
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"Suite YAML file not found: {yaml_path}")

        if suite_name is None:
            suite_name = yaml_file.stem

        # Load and parse YAML
        with open(yaml_file, 'r') as f:
            suite_config = yaml_file.read_text()

        # Create expectation suite from YAML
        suite = ExpectationSuite(
            expectation_suite_name=suite_name,
            expectations=[],
            meta={"created_from_yaml": True}
        )

        # Add to context
        self.context.add_expectation_suite(suite)

        self.logger.info(f"Created expectation suite '{suite_name}' from {yaml_path}")
        return suite_name


@task(name="validate_data_quality", description="Validate data quality using Great Expectations")
def validate_data_quality(
    df: pd.DataFrame,
    suite_name: str,
    data_asset_name: str = "validation_data",
    context_root_dir: Optional[str] = None,
    fail_on_error: bool = True
) -> Dict[str, Any]:
    """Prefect task to validate data quality using Great Expectations.

    Args:
        df: DataFrame to validate
        suite_name: Name of expectation suite to use
        data_asset_name: Name for the data asset
        context_root_dir: Directory for Great Expectations context
        fail_on_error: If True, task fails on validation errors

    Returns:
        Dictionary with validation results
    """
    validator = GreatExpectationsValidator(context_root_dir=context_root_dir)
    result = validator.validate_dataframe(df, suite_name, data_asset_name)

    if fail_on_error and not result.success:
        raise ValueError(
            f"Data validation failed for suite '{suite_name}': "
            f"{len(result.failed_expectations)}/{result.total_expectations} expectations failed"
        )

    return result.to_dict()


@task(name="load_validation_suite", description="Load Great Expectations suite from YAML")
def load_validation_suite(
    yaml_path: str,
    suite_name: Optional[str] = None,
    context_root_dir: Optional[str] = None
) -> str:
    """Prefect task to load expectation suite from YAML file.

    Args:
        yaml_path: Path to YAML suite file
        suite_name: Optional name for the suite
        context_root_dir: Directory for Great Expectations context

    Returns:
        Name of loaded suite
    """
    validator = GreatExpectationsValidator(context_root_dir=context_root_dir)
    return validator.create_suite_from_yaml(yaml_path, suite_name)


def get_validation_suites_dir() -> Path:
    """Get the directory containing validation suites."""
    return Path(__file__).parent.parent.parent / "ge_suites"


def list_available_suites() -> List[str]:
    """List all available validation suites."""
    suites_dir = get_validation_suites_dir()
    if not suites_dir.exists():
        return []

    return [f.stem for f in suites_dir.glob("*.yml")]


def validate_dataset(
    df: pd.DataFrame,
    dataset_type: str,
    run_context: Optional[RunContext] = None
) -> ValidationResult:
    """Validate a dataset using the appropriate suite.

    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset ("acs", "market_data", etc.)
        run_context: Optional RunContext for lineage tracking

    Returns:
        ValidationResult with validation results
    """
    # Map dataset types to suite names
    suite_mapping = {
        "acs": "acs_income_validation",
        "market_data": "market_data_validation",
        "census": "acs_income_validation",
    }

    suite_name = suite_mapping.get(dataset_type.lower())
    if not suite_name:
        raise ValueError(f"No validation suite found for dataset type: {dataset_type}")

    validator = GreatExpectationsValidator(run_context=run_context)
    return validator.validate_dataframe(df, suite_name)
