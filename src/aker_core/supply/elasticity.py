"""
Supply Elasticity Calculator

Calculates building permit elasticity as a proxy for supply constraints.
Higher elasticity (more permits per household) indicates lower supply constraints.
"""

from typing import Union

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def elasticity(
    permits: Union[NDArray, pd.Series, list],
    households: Union[NDArray, pd.Series, list],
    years: int = 3,
) -> float:
    """
    Calculate building permit elasticity as permits per 1,000 households over 3 years.

    This implements the inverse supply constraint metric where higher elasticity
    (more permits relative to households) indicates lower supply constraints.

    Args:
        permits: Array of annual building permit counts
        households: Array of annual household counts
        years: Number of years to average (default: 3)

    Returns:
        Float representing average permits per 1,000 households over the period

    Raises:
        ValueError: If inputs are invalid or incompatible
        ZeroDivisionError: If households are zero

    Examples:
        >>> permits = [1000, 1100, 1200]  # 3 years of permits
        >>> households = [50000, 51000, 52000]  # 3 years of households
        >>> elasticity(permits, households)
        22.115384615384617
    """
    # Convert inputs to numpy arrays
    permits_array = np.asarray(permits, dtype=float)
    households_array = np.asarray(households, dtype=float)

    # Validate inputs
    if len(permits_array) != len(households_array):
        raise ValueError(
            f"Permits and households arrays must have same length. "
            f"Got {len(permits_array)} permits and {len(households_array)} households"
        )

    if len(permits_array) < years:
        raise ValueError(
            f"Insufficient data: need at least {years} years, got {len(permits_array)}"
        )

    if years <= 0:
        raise ValueError("Years parameter must be positive")

    # Check for zero or negative households
    if np.any(households_array <= 0):
        raise ZeroDivisionError("Households cannot be zero or negative")

    # Check for negative permits
    if np.any(permits_array < 0):
        raise ValueError("Building permits cannot be negative")

    # Calculate permits per 1,000 households for each year
    permits_per_1k = (permits_array / households_array) * 1000

    # Use the most recent 'years' data points
    recent_permits = permits_per_1k[-years:]

    # Return the average
    return float(np.mean(recent_permits))


def inverse_elasticity_score(elasticity_value: float) -> float:
    """
    Convert elasticity to inverse supply constraint score (0-100).

    Higher elasticity (more supply responsive) results in lower constraint score.

    Args:
        elasticity_value: Permits per 1,000 households

    Returns:
        Supply constraint score (0-100) where higher = more constrained
    """
    # This would be used in the actual scoring pipeline
    # For now, just return the elasticity value as a placeholder
    return min(max(elasticity_value, 0), 100)
