"""Tests for the unified validation stack."""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from aker_core.validation import (
    SchemaValidator,
    ValidationFailure,
    ValidationResult,
    ValidationSummary,
    list_available_suites,
    validate_data_quality,
    validate_dataset,
)


@pytest.fixture
def sample_acs_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["New York, NY", "Los Angeles, CA", "Chicago, IL"],
            "b19013_001e": [75000, 65000, 55000],
            "b01003_001e": [8500000, 4000000, 2700000],
            "data_year": [2022, 2022, 2022],
            "source": ["census_api", "census_api", "census_api"],
            "ingested_at": pd.Timestamp.now(),
            "as_of": "2025-01",
        }
    )


@pytest.fixture
def invalid_acs_data(sample_acs_data: pd.DataFrame) -> pd.DataFrame:
    df = sample_acs_data.copy()
    df.loc[1, "name"] = None
    df.loc[2, "b19013_001e"] = -10
    return df


class TestValidationResult:
    def test_success_summary(self, sample_acs_data: pd.DataFrame) -> None:
        result = validate_dataset(sample_acs_data, "acs")
        payload = result.to_dict()

        assert result.success is True
        assert payload["success"] is True
        assert payload["failed_expectations"] == 0
        assert payload["failure_rate"] == 0.0

    def test_failure_summary(self, invalid_acs_data: pd.DataFrame) -> None:
        result = validate_dataset(invalid_acs_data, "acs")
        payload = result.to_dict()

        assert result.success is False
        assert payload["failed_expectations"] > 0
        assert payload["successful_expectations"] < payload["total_expectations"]
        assert result.failed_expectations  # contains details

    def test_pydantic_like_payload_shape(self, sample_acs_data: pd.DataFrame) -> None:
        result = validate_dataset(sample_acs_data, "acs")
        payload = result.to_dict()
        assert payload["success"] is True
        # payload carries direct fields now (no marshmallow)
        assert set(["dataset", "schema", "success", "total_expectations", "successful_expectations", "failed_expectations"]).issubset(payload.keys())


class TestSchemaValidator:
    def test_custom_schema_registration(self) -> None:
        schema = pa.DataFrameSchema(
            {
                "value": pa.Column(pa.Int64, checks=pa.Check.ge(0)),
            },
            strict=True,
            coerce=True,
        )
        validator = SchemaValidator(schemas={"custom": schema})

        df = pd.DataFrame({"value": [1, 2, 3]})
        result = validator.validate_dataframe(df, "custom")
        assert result.success is True

        df_invalid = pd.DataFrame({"value": [1, -1, 2]})
        result_invalid = validator.validate_dataframe(df_invalid, "custom")
        assert result_invalid.success is False
        assert result_invalid.failed_expectations


class TestValidateDataQualityTask:
    def test_task_success(self, sample_acs_data: pd.DataFrame) -> None:
        payload = validate_data_quality.fn(sample_acs_data, "acs", fail_on_error=True)
        assert payload["success"] is True

    def test_task_failure(self, invalid_acs_data: pd.DataFrame) -> None:
        with pytest.raises(ValueError):
            validate_data_quality.fn(invalid_acs_data, "acs", fail_on_error=True)

    def test_task_warning_mode(self, invalid_acs_data: pd.DataFrame) -> None:
        payload = validate_data_quality.fn(invalid_acs_data, "acs", fail_on_error=False)
        assert payload["success"] is False


class TestValidateDataset:
    def test_dataset_aliases(self, sample_acs_data: pd.DataFrame) -> None:
        # acs and census map to the same schema
        assert validate_dataset(sample_acs_data, "acs").success is True
        assert validate_dataset(sample_acs_data, "census").success is True

    def test_unknown_dataset(self, sample_acs_data: pd.DataFrame) -> None:
        with pytest.raises(KeyError):
            validate_dataset(sample_acs_data, "unknown_dataset")


class TestUtilities:
    def test_list_available_suites(self) -> None:
        suites = list_available_suites()
        assert "acs" in suites
        assert "market_data" in suites
        assert "permits" in suites

    def test_validation_failure_model(self) -> None:
        failure = ValidationFailure(column="col", check="gte", failure_case="-1", index=5)
        summary = ValidationSummary(
            dataset="test",
            schema_name="custom",
            success=False,
            total_checks=3,
            failure_count=1,
            validated_rows=2,
            failures=[failure],
        )
        result = ValidationResult(summary)
        assert result.success is False
        assert result.failure_rate == pytest.approx(1 / 3)
        assert result.failed_expectations[0]["column"] == "col"
