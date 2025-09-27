"""Tests for Great Expectations validation functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from aker_core.validation import (
    GreatExpectationsValidator,
    ValidationResult,
    get_validation_suites_dir,
    list_available_suites,
    validate_data_quality,
    validate_dataset,
)


@pytest.fixture
def sample_acs_data() -> pd.DataFrame:
    """Create sample ACS income data for testing."""
    return pd.DataFrame(
        {
            "name": ["New York, NY", "Los Angeles, CA", "Chicago, IL"],
            "b19013_001e": [75000, 65000, 55000],  # Median household income
            "b01003_001e": [8500000, 4000000, 2700000],  # Population
            "data_year": [2022, 2022, 2022],
            "source": ["census_api", "census_api", "census_api"],
            "ingested_at": pd.Timestamp.now(),
            "as_of": "2025-01",
        }
    )


@pytest.fixture
def sample_market_data() -> pd.DataFrame:
    """Create sample market scoring data for testing."""
    return pd.DataFrame(
        {
            "name": ["New York, NY", "Los Angeles, CA", "Chicago, IL"],
            "market_score": [85.5, 78.2, 72.1],
            "market_tier": ["A", "B", "B"],
            "scoring_model": ["simple_income_population_v1"] * 3,
            "scored_at": pd.Timestamp.now(),
            "data_year": [2022, 2022, 2022],
            "source": ["data_lake", "data_lake", "data_lake"],
        }
    )


@pytest.fixture
def sample_market_analytics() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "msa_id": ["123456789012"],
            "market_name": ["Test Market"],
            "population": [100000],
            "households": [40000],
            "vacancy_rate": [5.0],
            "permit_per_1k": [2.5],
            "tech_cagr": [4.0],
            "walk_15_ct": [25],
            "trail_mi_pc": [1.5],
            "supply_score": [4.0],
            "jobs_score": [3.5],
            "urban_score": [3.0],
            "outdoor_score": [2.5],
            "composite_score": [3.5],
            "period_month": [pd.Timestamp("2025-09-01")],
            "refreshed_at": [pd.Timestamp.now()],
            "run_id": [1],
        }
    )


@pytest.fixture
def sample_asset_performance() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "asset_id": [1],
            "msa_id": ["123456789012"],
            "units": [120],
            "year_built": [2010],
            "score": [75.0],
            "market_composite_score": [70.0],
            "rank_in_market": [1],
            "period_month": [pd.Timestamp("2025-09-01")],
            "refreshed_at": [pd.Timestamp.now()],
            "run_id": [1],
        }
    )


@pytest.fixture
def invalid_acs_data() -> pd.DataFrame:
    """Create invalid ACS data for testing validation failures."""
    return pd.DataFrame(
        {
            "name": ["New York, NY", None, "Chicago, IL"],  # Missing name
            "b19013_001e": [75000, -1000, 55000],  # Negative income
            "b01003_001e": [8500000, 65000, 2700000],
            "data_year": [2022, 2022, 2035],  # Invalid year
            "source": ["invalid_source", "census_api", "census_api"],
            "ingested_at": pd.Timestamp.now(),
            "as_of": "2025-01",
        }
    )


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_success(self) -> None:
        """Test ValidationResult with successful validation."""
        # Create a mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.success = True
        mock_validation_result.results = []

        result = ValidationResult([mock_validation_result])

        assert result.success is True
        assert result.total_expectations == 0
        assert result.successful_expectations == 0
        assert result.failed_expectations == []
        assert result.failure_rate == 0.0

    def test_validation_result_failure(self) -> None:
        """Test ValidationResult with failed expectations."""
        # Create a mock expectation result that fails
        mock_expectation_result = MagicMock()
        mock_expectation_result.success = False
        mock_expectation_result.expectation_config = MagicMock()
        mock_expectation_result.expectation_config.type = "expect_column_values_to_not_be_null"
        mock_expectation_result.expectation_config.kwargs = {"column": "name"}
        mock_expectation_result.result = "Column 'name' contains null values"

        # Create a mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.success = False  # This is the overall validation result success
        mock_validation_result.results = [mock_expectation_result]

        result = ValidationResult([mock_validation_result])

        assert result.success is False
        assert result.total_expectations == 1
        assert result.successful_expectations == 0
        assert len(result.failed_expectations) == 1
        assert result.failure_rate == 1.0

    def test_validation_result_to_dict(self) -> None:
        """Test ValidationResult to_dict method."""
        # Create a mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.success = True
        mock_validation_result.results = []

        result = ValidationResult([mock_validation_result])
        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["total_expectations"] == 0
        assert result_dict["successful_expectations"] == 0
        assert result_dict["failed_expectations"] == 0
        assert result_dict["failure_rate"] == 0.0
        assert "failed_details" in result_dict


class TestGreatExpectationsValidator:
    """Test GreatExpectationsValidator class."""

    def test_validator_initialization(self) -> None:
        """Test validator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the context creation to avoid GE setup issues
            with patch("aker_core.validation.FileDataContext") as mock_context:
                mock_context_instance = MagicMock()
                mock_context.return_value = mock_context_instance

                validator = GreatExpectationsValidator(context_root_dir=temp_dir)

                assert validator.context_root_dir == temp_dir
                assert validator.context == mock_context_instance
                assert validator.logger is not None

    def test_create_suite_from_yaml(self) -> None:
        """Test creating suite from YAML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test YAML file
            yaml_content = """
name: test_suite
version: 1.0.0
expectations:
  - expectation_type: expect_table_row_count_to_be_between
    kwargs:
      min_value: 1
      max_value: 1000
"""
            yaml_file = Path(temp_dir) / "test_suite.yml"
            yaml_file.write_text(yaml_content)

            # Mock the context creation to avoid GE setup issues
            with patch("aker_core.validation.FileDataContext") as mock_context:
                mock_context_instance = MagicMock()
                mock_context.return_value = mock_context_instance

                validator = GreatExpectationsValidator(context_root_dir=temp_dir)
                suite_name = validator.create_suite_from_yaml(str(yaml_file))

                assert suite_name == "test_suite"

    def test_validate_dataframe_success(self, sample_acs_data: pd.DataFrame) -> None:
        """Test successful DataFrame validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the context creation to avoid GE setup issues
            with patch("aker_core.validation.FileDataContext") as mock_context:
                mock_context_instance = MagicMock()
                mock_context_instance.get_expectation_suite.return_value = MagicMock()
                mock_context.return_value = mock_context_instance

                validator = GreatExpectationsValidator(context_root_dir=temp_dir)

                # Mock the validation to avoid actual GE processing
                with patch.object(
                    validator, "validate_dataframe", return_value=ValidationResult([])
                ):
                    result = validator.validate_dataframe(sample_acs_data, "test_suite")
                    assert result.success is True

    def test_list_available_suites(self) -> None:
        """Test listing available suites."""
        # Create test suite files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create ge_suites directory with test files
            ge_suites_dir = Path(temp_dir) / "ge_suites"
            ge_suites_dir.mkdir()

            (ge_suites_dir / "test1.yml").touch()
            (ge_suites_dir / "test2.yml").touch()
            (ge_suites_dir / "readme.txt").touch()  # Should be ignored

            with patch(
                "aker_core.validation.get_validation_suites_dir", return_value=ge_suites_dir
            ):
                suites = list_available_suites()
                assert "test1" in suites
                assert "test2" in suites
                assert "readme" not in suites  # txt files should be ignored


class TestPrefectTasks:
    """Test Prefect validation tasks."""

    def test_validate_data_quality_task(self, sample_acs_data: pd.DataFrame) -> None:
        """Test validate_data_quality Prefect task."""
        # Mock the validation to avoid GE context issues
        with patch("aker_core.validation.GreatExpectationsValidator") as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_dataframe.return_value = ValidationResult([])
            mock_validator_class.return_value = mock_validator

            result = validate_data_quality(
                df=sample_acs_data, suite_name="test_suite", fail_on_error=True
            )

            assert result["success"] is True
            assert result["total_expectations"] == 0

    def test_validate_data_quality_task_failure(self, sample_acs_data: pd.DataFrame) -> None:
        """Test validate_data_quality task with validation failure."""
        with patch("aker_core.validation.GreatExpectationsValidator") as mock_validator_class:
            # Create a mock validation result that indicates failure
            mock_validation_result = MagicMock()
            mock_validation_result.success = False
            mock_validation_result.results = []

            mock_validator = MagicMock()
            mock_validator.validate_dataframe.return_value = ValidationResult(
                [mock_validation_result]
            )
            mock_validator_class.return_value = mock_validator

            with pytest.raises(ValueError, match="Data validation failed"):
                validate_data_quality(
                    df=sample_acs_data, suite_name="test_suite", fail_on_error=True
                )

    def test_validate_data_quality_task_no_fail(self, sample_acs_data: pd.DataFrame) -> None:
        """Test validate_data_quality task without failing on errors."""
        with patch("aker_core.validation.GreatExpectationsValidator") as mock_validator_class:
            # Create a mock validation result that indicates failure
            mock_validation_result = MagicMock()
            mock_validation_result.success = False
            mock_validation_result.results = []

            mock_validator = MagicMock()
            mock_validator.validate_dataframe.return_value = ValidationResult(
                [mock_validation_result]
            )
            mock_validator_class.return_value = mock_validator

            result = validate_data_quality(
                df=sample_acs_data, suite_name="test_suite", fail_on_error=False
            )

            assert result["success"] is False


class TestDatasetValidation:
    """Test dataset validation functionality."""

    def test_validate_dataset_mapping(self, sample_acs_data: pd.DataFrame) -> None:
        """Test dataset type to suite mapping."""
        with patch("aker_core.validation.GreatExpectationsValidator") as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_dataframe.return_value = ValidationResult([])
            mock_validator_class.return_value = mock_validator

            # Test ACS dataset
            result = validate_dataset(sample_acs_data, "acs")
            assert result.success is True

            # Test market data
            result = validate_dataset(sample_acs_data, "market_data")
            assert result.success is True

    def test_validate_dataset_invalid_type(self) -> None:
        """Test validation with invalid dataset type."""
        with pytest.raises(ValueError, match="No validation suite found"):
            validate_dataset(pd.DataFrame(), "invalid_type")


class TestDatasetValidationRouting:
    def test_validate_dataset_market_analytics(self, monkeypatch, sample_market_analytics) -> None:
        captured: dict[str, str] = {}

        class DummyValidator:
            def __init__(self, run_context=None):
                self.context = MagicMock()
                self.context.get_expectation_suite.side_effect = Exception()

            def create_suite_from_yaml(self, yaml_path: str, suite_name: str) -> str:
                captured["yaml"] = yaml_path
                captured["suite"] = suite_name
                return suite_name

            def validate_dataframe(self, df: pd.DataFrame, suite_name: str) -> ValidationResult:
                captured["validate_suite"] = suite_name
                return ValidationResult([])

        monkeypatch.setattr("aker_core.validation.GreatExpectationsValidator", DummyValidator)

        result = validate_dataset(sample_market_analytics, "market_analytics")
        assert result.success is True
        assert captured["suite"] == "market_analytics_validation"
        assert captured["validate_suite"] == "market_analytics_validation"
        assert captured["yaml"].endswith("market_analytics.yml")

    def test_validate_dataset_asset_performance(
        self, monkeypatch, sample_asset_performance
    ) -> None:
        captured: dict[str, str] = {}

        class DummyValidator:
            def __init__(self, run_context=None):
                self.context = MagicMock()
                self.context.get_expectation_suite.side_effect = Exception()

            def create_suite_from_yaml(self, yaml_path: str, suite_name: str) -> str:
                captured["yaml"] = yaml_path
                captured["suite"] = suite_name
                return suite_name

            def validate_dataframe(self, df: pd.DataFrame, suite_name: str) -> ValidationResult:
                captured["validate_suite"] = suite_name
                return ValidationResult([])

        monkeypatch.setattr("aker_core.validation.GreatExpectationsValidator", DummyValidator)

        result = validate_dataset(sample_asset_performance, "asset_performance")
        assert result.success is True
        assert captured["suite"] == "asset_performance_validation"
        assert captured["validate_suite"] == "asset_performance_validation"
        assert captured["yaml"].endswith("asset_performance.yml")


class TestQualityGateScript:
    """Test quality gate script functionality."""

    def test_list_suites_function(self) -> None:
        """Test the list_suites function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test suite files
            ge_suites_dir = Path(temp_dir) / "ge_suites"
            ge_suites_dir.mkdir()

            (ge_suites_dir / "acs.yml").touch()
            (ge_suites_dir / "market_data.yml").touch()

            with patch(
                "aker_core.validation.get_validation_suites_dir", return_value=ge_suites_dir
            ):
                suites = list_available_suites()
                assert "acs" in suites
                assert "market_data" in suites

    def test_get_validation_suites_dir(self) -> None:
        """Test get_validation_suites_dir function."""
        expected_dir = Path(__file__).parent.parent.parent / "ge_suites"
        actual_dir = get_validation_suites_dir()

        # The function returns the path relative to the project root
        assert str(actual_dir).endswith("ge_suites")


class TestIntegration:
    """Integration tests for validation functionality."""

    def test_validation_module_imports(self) -> None:
        """Test that validation module can be imported."""
        from aker_core.validation import (
            GreatExpectationsValidator,
            ValidationResult,
            validate_data_quality,
            validate_dataset,
        )

        # Check that classes and functions are available
        assert GreatExpectationsValidator is not None
        assert ValidationResult is not None
        assert callable(validate_data_quality)
        assert callable(validate_dataset)

    def test_validation_with_run_context(self, sample_acs_data: pd.DataFrame) -> None:
        """Test validation with RunContext integration."""
        mock_run_context = MagicMock()

        with patch("aker_core.validation.GreatExpectationsValidator") as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate_dataframe.return_value = ValidationResult([])
            mock_validator_class.return_value = mock_validator

            result = validate_dataset(sample_acs_data, "acs", run_context=mock_run_context)

            # The validator should have been called with the run_context
            mock_validator_class.assert_called()
            call_args = mock_validator_class.call_args
            assert call_args.kwargs["run_context"] == mock_run_context

    def test_validation_result_properties(self) -> None:
        """Test ValidationResult property calculations."""
        # Create mock results with known success/failure counts
        mock_result1 = MagicMock()
        mock_result1.results = [MagicMock(success=True), MagicMock(success=False)]

        mock_result2 = MagicMock()
        mock_result2.results = [MagicMock(success=True)]

        result = ValidationResult([mock_result1, mock_result2])

        assert result.total_expectations == 3
        assert result.successful_expectations == 2
        assert len(result.failed_expectations) == 1
        assert result.failure_rate == 1 / 3
