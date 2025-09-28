"""
Common utility functions for the Aker Property Model.

This module provides reusable utility functions for common operations
across all modules in the application.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .exceptions import validation_error


def safe_float_conversion(value: Any, field_name: str = "value") -> float:
    """
    Safely convert a value to float with validation.

    Args:
        value: Value to convert
        field_name: Name of the field for error messages

    Returns:
        Float value

    Raises:
        ValidationError: If conversion fails or result is invalid
    """
    try:
        if isinstance(value, str):
            # Handle percentage strings
            if value.endswith('%'):
                value = value[:-1]
            # Handle currency strings
            if value.startswith('$'):
                value = value[1:]

        result = float(value)

        if not (0 <= result < 1e12):  # Reasonable bounds for financial values
            raise validation_error(field_name, value, "value out of reasonable range")

        return result
    except (ValueError, TypeError) as e:
        raise validation_error(field_name, value, f"cannot convert to float: {e}")


def safe_int_conversion(value: Any, field_name: str = "value") -> int:
    """
    Safely convert a value to int with validation.

    Args:
        value: Value to convert
        field_name: Name of the field for error messages

    Returns:
        Integer value

    Raises:
        ValidationError: If conversion fails or result is invalid
    """
    try:
        result = int(float(value))  # Handle string floats

        if not (0 <= result < 1e9):  # Reasonable bounds
            raise validation_error(field_name, value, "value out of reasonable range")

        return result
    except (ValueError, TypeError) as e:
        raise validation_error(field_name, value, f"cannot convert to int: {e}")


def format_currency(value: Union[float, int, Decimal], precision: int = 0) -> str:
    """
    Format a numeric value as currency.

    Args:
        value: Numeric value to format
        precision: Number of decimal places

    Returns:
        Formatted currency string
    """
    try:
        numeric_value = float(value)
        format_spec = f"{numeric_value:,.{precision}f}"
        return f"${format_spec}"
    except (ValueError, TypeError):
        return "$0"


def format_percentage(value: Union[float, int, Decimal], precision: int = 1) -> str:
    """
    Format a numeric value as percentage.

    Args:
        value: Numeric value to format (0.25 for 25%)
        precision: Number of decimal places

    Returns:
        Formatted percentage string
    """
    try:
        numeric_value = float(value) * 100
        return f"{numeric_value:.{precision}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def calculate_percentage_change(old_value: Union[float, int], new_value: Union[float, int]) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value
        new_value: New value

    Returns:
        Percentage change (positive for increase, negative for decrease)
    """
    try:
        old_val = float(old_value)
        new_val = float(new_value)

        if old_val == 0:
            return float('inf') if new_val != 0 else 0.0

        return ((new_val - old_val) / old_val) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def hash_dict(data: Dict[str, Any]) -> str:
    """
    Create a deterministic hash of a dictionary for caching.

    Args:
        data: Dictionary to hash

    Returns:
        SHA256 hash as hex string
    """
    # Sort keys for deterministic hashing
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present and not None/empty.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            raise validation_error(field, data.get(field), "field is required")


def sanitize_string(value: str, max_length: int = 255, allow_empty: bool = False) -> str:
    """
    Sanitize a string value with length limits.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are allowed

    Returns:
        Sanitized string

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise validation_error("input", value, "must be a string")

    if not allow_empty and not value.strip():
        raise validation_error("input", value, "cannot be empty")

    sanitized = value.strip()
    if len(sanitized) > max_length:
        raise validation_error("input", value, f"exceeds maximum length of {max_length}")

    return sanitized


def create_timestamp() -> str:
    """
    Create a standardized timestamp string.

    Returns:
        ISO format timestamp string
    """
    return datetime.now().isoformat()


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        import uuid
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        data: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def safe_divide(numerator: Union[float, int], denominator: Union[float, int], default: float = 0.0) -> float:
    """
    Safely divide two numbers with default for division by zero.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if denominator is zero

    Returns:
        Division result or default value
    """
    try:
        num_val = float(numerator)
        den_val = float(denominator)

        if den_val == 0:
            return default

        return num_val / den_val
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def normalize_to_range(value: float, min_val: float, max_val: float, target_min: float = 0, target_max: float = 100) -> float:
    """
    Normalize a value from one range to another.

    Args:
        value: Value to normalize
        min_val: Minimum value of source range
        max_val: Maximum value of source range
        target_min: Minimum value of target range (default: 0)
        target_max: Maximum value of target range (default: 100)

    Returns:
        Normalized value in target range
    """
    if min_val >= max_val:
        raise ValueError("min_val must be less than max_val")

    # Clamp value to source range
    clamped_value = max(min_val, min(max_val, value))

    # Normalize to 0-1 range
    normalized = (clamped_value - min_val) / (max_val - min_val)

    # Scale to target range
    return target_min + (normalized * (target_max - target_min))
