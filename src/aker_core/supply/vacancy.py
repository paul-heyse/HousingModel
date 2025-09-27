"""
Supply Vacancy Calculator

Calculates rental vacancy rates as a proxy for supply constraints.
Lower vacancy rates indicate higher supply constraints (tighter markets).
"""

from typing import Dict, Optional, Union

import numpy as np
import pandas as pd


def vacancy(
    hud_data: Union[pd.DataFrame, Dict],
    msa_boundaries: Optional[Union[pd.DataFrame, Dict]] = None,
    vacancy_type: str = "rental",
) -> float:
    """
    Calculate rental vacancy rates from HUD data with optional geographic aggregation.

    This implements the inverse supply constraint metric where lower vacancy rates
    indicate higher supply constraints (tighter markets with less available supply).

    Args:
        hud_data: HUD vacancy data (DataFrame or dict with columns: year, vacancy_rate, geography)
        msa_boundaries: Optional geographic boundaries for aggregation (DataFrame or dict)
        vacancy_type: Type of vacancy to calculate ('rental', 'multifamily', 'overall')

    Returns:
        Float representing vacancy rate as percentage (0-100)

    Raises:
        ValueError: If inputs are invalid or incompatible
        KeyError: If required columns are missing

    Examples:
        >>> hud_data = {
        ...     'year': [2020, 2021, 2022],
        ...     'vacancy_rate': [5.2, 4.8, 4.5],
        ...     'geography': ['MSA001', 'MSA001', 'MSA001']
        ... }
        >>> vacancy(hud_data)
        4.833333333333333
    """
    # Convert HUD data to DataFrame
    if isinstance(hud_data, dict):
        hud_df = pd.DataFrame(hud_data)
    elif isinstance(hud_data, pd.DataFrame):
        hud_df = hud_data.copy()
    else:
        raise ValueError("hud_data must be a pandas DataFrame or dictionary")

    # Validate required columns
    required_cols = ["year", "vacancy_rate"]
    if vacancy_type != "overall":
        required_cols.append("geography")

    missing_cols = [col for col in required_cols if col not in hud_df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Validate vacancy_type
    valid_types = ["rental", "multifamily", "overall"]
    if vacancy_type not in valid_types:
        raise ValueError(f"vacancy_type must be one of {valid_types}, got {vacancy_type}")

    # Filter by vacancy type if specified
    if vacancy_type != "overall":
        # For now, assume all data is of the requested type
        # In practice, this would filter based on data source indicators
        pass

    # Handle geographic aggregation if boundaries provided
    if msa_boundaries is not None:
        # This would aggregate data to MSA level
        # For now, assume data is already at MSA level
        pass

    # Calculate average vacancy rate across all years
    vacancy_rates = hud_df["vacancy_rate"].values

    # Validate vacancy rates are reasonable (0-100%)
    if np.any((vacancy_rates < 0) | (vacancy_rates > 100)):
        raise ValueError("Vacancy rates must be between 0 and 100")

    # Handle missing values
    valid_rates = vacancy_rates[~np.isnan(vacancy_rates)]

    if len(valid_rates) == 0:
        raise ValueError("No valid vacancy rate data available")

    # Return the average vacancy rate
    return float(np.mean(valid_rates))


def inverse_vacancy_score(vacancy_rate: float) -> float:
    """
    Convert vacancy rate to inverse supply constraint score (0-100).

    Lower vacancy rates indicate higher supply constraints (tighter markets).

    Args:
        vacancy_rate: Vacancy rate as percentage (0-100)

    Returns:
        Supply constraint score (0-100) where higher = more constrained
    """
    # Higher vacancy = lower constraint score
    # This implements the inverse relationship
    return min(max(100 - vacancy_rate, 0), 100)
