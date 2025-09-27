"""
Supply Lease-Up Time-on-Market Calculator

Calculates multi-family lease-up time-on-market as a proxy for supply constraints.
Shorter lease-up times indicate higher supply constraints (tighter markets).
"""

from typing import Dict, Optional, Union

import numpy as np
import pandas as pd


def leaseup_tom(
    lease_data: Union[pd.DataFrame, Dict],
    property_filters: Optional[Dict] = None,
    time_window_days: int = 90,
) -> float:
    """
    Calculate multi-family lease-up time-on-market from lease transaction data.

    This implements the inverse supply constraint metric where shorter lease-up times
    indicate higher supply constraints (properties lease up faster in tight markets).

    Args:
        lease_data: Lease transaction data (DataFrame or dict with lease_date, property_id, days_on_market)
        property_filters: Optional filters for property types, sizes, etc.
        time_window_days: Analysis window in days (default: 90)

    Returns:
        Float representing average days on market for lease-up

    Raises:
        ValueError: If inputs are invalid or incompatible
        KeyError: If required columns are missing

    Examples:
        >>> lease_data = {
        ...     'lease_date': pd.date_range('2023-01-01', periods=100, freq='D'),
        ...     'property_id': ['PROP001'] * 50 + ['PROP002'] * 50,
        ...     'days_on_market': np.random.randint(10, 60, 100)
        ... }
        >>> leaseup_tom(lease_data)
        35.23
    """
    # Convert lease data to DataFrame
    if isinstance(lease_data, dict):
        lease_df = pd.DataFrame(lease_data)
    elif isinstance(lease_data, pd.DataFrame):
        lease_df = lease_data.copy()
    else:
        raise ValueError("lease_data must be a pandas DataFrame or dictionary")

    # Validate required columns
    required_cols = ["lease_date", "days_on_market"]
    if "property_id" not in lease_df.columns:
        # Generate property IDs if not present (for testing/demo)
        lease_df["property_id"] = "UNKNOWN"

    missing_cols = [col for col in required_cols if col not in lease_df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Apply property filters if provided
    if property_filters:
        for key, value in property_filters.items():
            if key in lease_df.columns:
                if isinstance(value, list):
                    lease_df = lease_df[lease_df[key].isin(value)]
                else:
                    lease_df = lease_df[lease_df[key] == value]

    # Convert lease_date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(lease_df["lease_date"]):
        lease_df["lease_date"] = pd.to_datetime(lease_df["lease_date"])

    # Filter to recent time window
    cutoff_date = lease_df["lease_date"].max() - pd.Timedelta(days=time_window_days)
    recent_leases = lease_df[lease_df["lease_date"] >= cutoff_date]

    if len(recent_leases) < 2:
        raise ValueError(f"No lease data available in the last {time_window_days} days")

    # Get days on market values
    days_on_market = recent_leases["days_on_market"].values

    # Validate days on market are reasonable (0-365 days)
    if np.any((days_on_market < 0) | (days_on_market > 365)):
        raise ValueError("Days on market must be between 0 and 365")

    # Handle missing values
    valid_days = days_on_market[~np.isnan(days_on_market)]

    if len(valid_days) == 0:
        raise ValueError("No valid days on market data available")

    # Calculate median days on market (more robust than mean for lease-up times)
    try:
        median = np.quantile(valid_days, 0.5, method="lower")
    except TypeError:  # pragma: no cover - NumPy < 1.22
        median = np.quantile(valid_days, 0.5, interpolation="lower")
    median_tom = float(median)

    return median_tom


def inverse_leaseup_score(days_on_market: float) -> float:
    """
    Convert lease-up time to inverse supply constraint score (0-100).

    Shorter lease-up times indicate higher supply constraints (tighter markets).

    Args:
        days_on_market: Average/median days on market for lease-up

    Returns:
        Supply constraint score (0-100) where higher = more constrained
    """
    # Normalize days on market to 0-100 scale
    # Assume 0 days = 100 (very constrained), 90 days = 0 (very loose)
    max_days = 90  # Beyond this, market is considered very loose
    normalized_score = max(0, 100 - (days_on_market / max_days) * 100)
    return min(normalized_score, 100)
