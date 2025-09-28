"""
Common exception classes for the Aker Property Model.

This module provides a consistent exception hierarchy for error handling
across all modules in the application.
"""

from __future__ import annotations


class AkerBaseException(Exception):
    """Base exception class for all Aker Property Model errors."""

    def __init__(self, message: str, details: dict[str, any] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(AkerBaseException):
    """Raised when input validation fails."""
    pass


class DatabaseError(AkerBaseException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AkerBaseException):
    """Raised when configuration is invalid or missing."""
    pass


class AuthenticationError(AkerBaseException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AkerBaseException):
    """Raised when authorization fails."""
    pass


class DataProcessingError(AkerBaseException):
    """Raised when data processing operations fail."""
    pass


class ExternalAPIError(AkerBaseException):
    """Raised when external API calls fail."""
    pass


class FileProcessingError(AkerBaseException):
    """Raised when file processing operations fail."""
    pass


class BusinessLogicError(AkerBaseException):
    """Raised when business logic validation fails."""
    pass


class PerformanceError(AkerBaseException):
    """Raised when performance thresholds are exceeded."""
    pass


# Convenience functions for common error scenarios
def validation_error(field: str, value: any, reason: str) -> ValidationError:
    """Create a validation error with field context."""
    return ValidationError(
        f"Validation failed for field '{field}': {reason}",
        details={"field": field, "value": value, "reason": reason}
    )


def database_error(operation: str, table: str = None, details: dict = None) -> DatabaseError:
    """Create a database error with operation context."""
    message = f"Database operation '{operation}' failed"
    if table:
        message += f" on table '{table}'"

    error_details = {"operation": operation}
    if table:
        error_details["table"] = table
    if details:
        error_details.update(details)

    return DatabaseError(message, details=error_details)


def configuration_error(setting: str, expected_type: str = None, details: dict = None) -> ConfigurationError:
    """Create a configuration error with setting context."""
    message = f"Configuration error for setting '{setting}'"
    if expected_type:
        message += f": expected {expected_type}"

    error_details = {"setting": setting}
    if expected_type:
        error_details["expected_type"] = expected_type
    if details:
        error_details.update(details)

    return ConfigurationError(message, details=error_details)


def external_api_error(service: str, operation: str, status_code: int = None, details: dict = None) -> ExternalAPIError:
    """Create an external API error with service context."""
    message = f"External API call to '{service}' failed"
    if operation:
        message += f" for operation '{operation}'"
    if status_code:
        message += f" with status code {status_code}"

    error_details = {"service": service, "operation": operation}
    if status_code:
        error_details["status_code"] = status_code
    if details:
        error_details.update(details)

    return ExternalAPIError(message, details=error_details)


def business_logic_error(rule: str, value: any, threshold: any = None, details: dict = None) -> BusinessLogicError:
    """Create a business logic error with rule context."""
    message = f"Business logic violation for rule '{rule}'"
    if threshold is not None:
        message += f": value {value} exceeds threshold {threshold}"

    error_details = {"rule": rule, "value": value}
    if threshold is not None:
        error_details["threshold"] = threshold
    if details:
        error_details.update(details)

    return BusinessLogicError(message, details=error_details)
