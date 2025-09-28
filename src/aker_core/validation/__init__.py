"""Unified data validation powered by Pandera and Pydantic."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Mapping, Optional

import pandas as pd
import pandera as pa
from pandera.errors import SchemaError, SchemaErrors
from prefect import task
from pydantic import BaseModel, Field

from aker_core.run import RunContext

from .schemas import (
    DATASET_SCHEMA_ALIASES,
    DATASET_SCHEMAS,
    SUPPLY_SUMMARY_SCHEMA,
    resolve_schema,
)

__all__ = [
    "SchemaValidator",
    "GreatExpectationsValidator",
    "ValidationFailure",
    "ValidationResult",
    "ValidationSummary",
    "list_available_suites",
    "validate_data_quality",
    "validate_dataset",
]

_logger = logging.getLogger(__name__)


class ValidationFailure(BaseModel):
    """Structured representation of a single validation failure."""

    column: Optional[str] = Field(default=None, description="Column associated with the failure")
    check: Optional[str] = Field(default=None, description="Name of the check that failed")
    failure_case: Optional[str] = Field(default=None, description="Observed failing value")
    index: Optional[int] = Field(default=None, description="Row index of the failing record")
    message: Optional[str] = Field(default=None, description="Human readable error message")


class ValidationSummary(BaseModel):
    """Summary information about a validation run."""

    dataset: str
    schema_name: str
    success: bool
    total_checks: int
    failure_count: int
    validated_rows: int
    failures: List[ValidationFailure] = Field(default_factory=list)

    @property
    def successful_checks(self) -> int:
        return max(self.total_checks - self.failure_count, 0)

    @property
    def failure_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.failure_count / self.total_checks


# Marshmallow schemas removed; payload is produced directly by to_dict()


def _estimate_total_checks(schema: pa.DataFrameSchema) -> int:
    column_checks = sum(len(col.checks or []) for col in schema.columns.values())
    schema_checks = len(schema.checks or [])
    return max(column_checks + schema_checks, 1)


class SchemaValidator:
    """Validate pandas DataFrames against registered Pandera schemas."""

    def __init__(
        self,
        *,
        schemas: Optional[Mapping[str, pa.DataFrameSchema]] = None,
        run_context: Optional[RunContext] = None,
    ) -> None:
        self._schemas: Dict[str, pa.DataFrameSchema] = dict(schemas or DATASET_SCHEMAS)
        self._run_context = run_context
        self.logger = logging.getLogger(f"{__name__}.SchemaValidator")

    def register_schema(self, name: str, schema: pa.DataFrameSchema) -> None:
        self._schemas[name] = schema

    def resolve(self, schema_name: str) -> pa.DataFrameSchema:
        if schema_name not in self._schemas:
            raise ValueError(f"No validation schema registered under '{schema_name}'")
        return self._schemas[schema_name]

    def validate_dataframe(self, df: pd.DataFrame, schema_name: str, *, dataset: Optional[str] = None) -> "ValidationResult":
        schema = self.resolve(schema_name)
        total_checks = _estimate_total_checks(schema)
        failures: List[ValidationFailure] = []
        success = True

        try:
            schema.validate(df, lazy=True, inplace=False)
        except SchemaErrors as exc:
            success = False
            failures.extend(_convert_failure_cases(exc.failure_cases))
        except SchemaError as exc:
            success = False
            failure = ValidationFailure(
                column=getattr(exc, "column", None),
                check=getattr(exc, "check", None),
                failure_case=str(getattr(exc, "failure_case", "")),
                message=str(exc),
            )
            failures.append(failure)

        summary = ValidationSummary(
            dataset=(dataset or schema_name),
            schema_name=schema_name,
            success=success,
            total_checks=total_checks,
            failure_count=len(failures),
            validated_rows=len(df),
            failures=failures,
        )

        result = ValidationResult(summary)
        self._log_result(result)
        return result

    def _log_result(self, result: "ValidationResult") -> None:
        if self._run_context is not None:
            try:
                self._run_context.log_lineage(
                    table=f"validation::{result.dataset}",
                    source="pandera",
                    url=None,
                    fetched_at=None,
                    hash=str(result.success),
                )
            except Exception:  # pragma: no cover - lineage logging is best effort
                self.logger.debug("RunContext lineage logging skipped for validation result")

        if result.success:
            self.logger.debug(
                "validation_success",
                extra={
                    "dataset": result.dataset,
                    "schema": result.schema,
                    "rows": result.validated_rows,
                    "checks": result.total_expectations,
                },
            )
        else:
            self.logger.warning(
                "validation_failure",
                extra={
                    "dataset": result.dataset,
                    "schema": result.schema,
                    "rows": result.validated_rows,
                    "failures": result.failed_expectations,
                },
            )


def _convert_failure_cases(failure_cases: pd.DataFrame) -> List[ValidationFailure]:
    if failure_cases is None or failure_cases.empty:
        return []
    failures: List[ValidationFailure] = []
    for _, row in failure_cases.iterrows():
        failures.append(
            ValidationFailure(
                column=row.get("column"),
                check=row.get("check"),
                failure_case=str(row.get("failure_case")),
                index=row.get("index") if pd.notna(row.get("index")) else None,
                message=row.get("schema_context"),
            )
        )
    return failures


class ValidationResult:
    """Wrapper providing backwards-compatible accessors for validation output."""

    def __init__(self, summary: ValidationSummary) -> None:
        self._summary = summary
        self._failures = [failure.model_dump() for failure in summary.failures]
        self.results: List[Any] = []  # kept for backwards compatibility with older code

    @property
    def dataset(self) -> str:
        return self._summary.dataset

    @property
    def schema(self) -> str:
        return self._summary.schema_name

    @property
    def success(self) -> bool:
        return self._summary.success

    @property
    def total_expectations(self) -> int:
        return self._summary.total_checks

    @property
    def successful_expectations(self) -> int:
        return self._summary.successful_checks

    @property
    def failed_expectations(self) -> List[Dict[str, Any]]:
        return self._failures

    @property
    def failure_rate(self) -> float:
        return self._summary.failure_rate

    @property
    def validated_rows(self) -> int:
        return self._summary.validated_rows

    def to_dict(self) -> Dict[str, Any]:
        # Preserve the historical output keys expected by downstream consumers
        return {
            "dataset": self.dataset,
            "schema": self.schema,
            "success": self.success,
            "total_expectations": self.total_expectations,
            "successful_expectations": self.successful_expectations,
            "failed_expectations": len(self.failed_expectations),
            "failure_rate": self.failure_rate,
            "validated_rows": self.validated_rows,
            "failures": self.failed_expectations,
        }


def list_available_suites() -> List[str]:
    """Return the list of dataset types with registered validation schemas."""
    keys: Iterable[str] = set(DATASET_SCHEMAS.keys()) | set(DATASET_SCHEMA_ALIASES.keys())
    return sorted(keys)


def _default_validator(run_context: Optional[RunContext] = None) -> SchemaValidator:
    return SchemaValidator(run_context=run_context)


@task(name="validate_data_quality", description="Validate a DataFrame using registered schemas")
def validate_data_quality(
    df: pd.DataFrame,
    dataset_type: str,
    *,
    fail_on_error: bool = True,
    run_context: Optional[RunContext] = None,
) -> Dict[str, Any]:
    """Validate data quality for a DataFrame and return a serialised result."""
    result = validate_dataset(df, dataset_type, run_context=run_context)

    if fail_on_error and not result.success:
        raise ValueError(
            f"Data validation failed for dataset '{dataset_type}': {len(result.failed_expectations)} failures"
        )

    return result.to_dict()


def validate_dataset(
    df: pd.DataFrame,
    dataset_type: str,
    run_context: Optional[RunContext] = None,
) -> ValidationResult:
    """Validate a DataFrame against the schema registered for the dataset type."""
    _ = resolve_schema(dataset_type)  # raises if the schema is unknown
    validator = _default_validator(run_context=run_context)
    schema_name = _canonical_schema_name(dataset_type)
    return validator.validate_dataframe(df, schema_name, dataset=dataset_type)


def _canonical_schema_name(dataset_type: str) -> str:
    key = dataset_type.lower()
    return DATASET_SCHEMA_ALIASES.get(key, key)


# Supply validation integration -------------------------------------------------

class SupplyValidationSuite:
    """Validate aggregate supply metrics using Pandera schemas."""

    def __init__(
        self,
        *,
        schema: pa.DataFrameSchema = SUPPLY_SUMMARY_SCHEMA,
        run_context: Optional[RunContext] = None,
    ) -> None:
        self.schema = schema
        self.validator = SchemaValidator(schemas={"supply_summary": schema}, run_context=run_context)

    def validate_supply_data(
        self,
        session,
        msa_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        from aker_core.database.supply import SupplyRepository

        repo = SupplyRepository(session)
        summary_stats = repo.get_supply_summary_stats(msa_ids)
        df = pd.DataFrame([summary_stats])
        result = self.validator.validate_dataframe(df, "supply_summary", dataset="supply_summary")
        return {
            "validation_success": result.success,
            "validation_report": result.to_dict(),
            "summary_stats": summary_stats,
        }


def run_supply_validation_cli(session, msa_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Command-line helper for validating supply metrics."""
    suite = SupplyValidationSuite()
    return suite.validate_supply_data(session, msa_ids)


# Backwards-compatibility alias until downstream code migrates away from GE naming
GreatExpectationsValidator = SchemaValidator
