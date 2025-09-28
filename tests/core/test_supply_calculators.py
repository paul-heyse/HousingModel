"""
Tests for Aker Core Supply Calculators

Tests the elasticity, vacancy, and lease-up time-on-market calculators
for the supply constraint pillar of the Aker Property Model.
"""

import numpy as np
import pandas as pd
import pytest

from aker_core.supply import elasticity, leaseup_tom, vacancy


class TestElasticityCalculator:
    """Test cases for the elasticity calculator."""

    def test_basic_elasticity_calculation(self):
        """Test basic elasticity calculation with sample data."""
        permits = [1000, 1100, 1200]  # 3 years of permits
        households = [50000, 51000, 52000]  # 3 years of households

        result = elasticity(permits, households)

        # Expected: (1000/50000 + 1100/51000 + 1200/52000) / 3 * 1000
        # = (0.02 + 0.02157 + 0.02308) / 3 * 1000 = 0.02155 * 1000 = 21.55
        expected = 21.55
        assert abs(result - expected) < 0.01

    def test_elasticity_with_different_years(self):
        """Test elasticity calculation with different averaging periods."""
        permits = [1000, 1100, 1200, 1300]  # 4 years
        households = [50000, 51000, 52000, 53000]

        # Test 3-year average (default)
        result_3yr = elasticity(permits, households, years=3)
        assert result_3yr > 0

        # Test 2-year average
        result_2yr = elasticity(permits, households, years=2)
        assert result_2yr > 0

    def test_elasticity_insufficient_data(self):
        """Test error handling for insufficient data."""
        permits = [1000]  # Only 1 year
        households = [50000]

        with pytest.raises(ValueError, match="Insufficient data"):
            elasticity(permits, households, years=3)

    def test_elasticity_zero_households(self):
        """Test error handling for zero households."""
        permits = [1000, 1100, 1200]
        households = [50000, 0, 52000]  # Zero households in middle year

        with pytest.raises(ZeroDivisionError):
            elasticity(permits, households)

    def test_elasticity_negative_permits(self):
        """Test error handling for negative permits."""
        permits = [1000, -100, 1200]  # Negative permits
        households = [50000, 51000, 52000]

        with pytest.raises(ValueError, match="Building permits cannot be negative"):
            elasticity(permits, households)

    def test_elasticity_array_mismatch(self):
        """Test error handling for mismatched array lengths."""
        permits = [1000, 1100]  # 2 values
        households = [50000, 51000, 52000]  # 3 values

        with pytest.raises(ValueError, match="same length"):
            elasticity(permits, households)

    def test_elasticity_pandas_input(self):
        """Test elasticity calculation with pandas Series input."""
        permits = pd.Series([1000, 1100, 1200])
        households = pd.Series([50000, 51000, 52000])

        result = elasticity(permits, households)
        assert isinstance(result, float)
        assert result > 0

    def test_elasticity_list_input(self):
        """Test elasticity calculation with list input."""
        permits = [1000, 1100, 1200]
        households = [50000, 51000, 52000]

        result = elasticity(permits, households)
        assert isinstance(result, float)
        assert result > 0


class TestVacancyCalculator:
    """Test cases for the vacancy calculator."""

    def test_basic_vacancy_calculation(self):
        """Test basic vacancy rate calculation."""
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, 4.8, 4.5],
            "geography": ["MSA001", "MSA001", "MSA001"],
        }

        result = vacancy(hud_data)

        # Expected: (5.2 + 4.8 + 4.5) / 3 = 4.833...
        expected = 4.833333333333333
        assert abs(result - expected) < 0.001

    def test_vacancy_invalid_rates(self):
        """Test error handling for invalid vacancy rates."""
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, -1.0, 4.5],  # Negative rate
            "geography": ["MSA001", "MSA001", "MSA001"],
        }

        with pytest.raises(ValueError, match="between 0 and 100"):
            vacancy(hud_data)

    def test_vacancy_missing_columns(self):
        """Test error handling for missing required columns."""
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, 4.8, 4.5],
            # Missing 'geography' column
        }

        with pytest.raises(KeyError, match="Missing required columns"):
            vacancy(hud_data)

    def test_vacancy_all_nan(self):
        """Test error handling for all NaN vacancy rates."""
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [np.nan, np.nan, np.nan],
            "geography": ["MSA001", "MSA001", "MSA001"],
        }

        with pytest.raises(ValueError, match="No valid vacancy rate data"):
            vacancy(hud_data)

    def test_vacancy_dataframe_input(self):
        """Test vacancy calculation with DataFrame input."""
        df = pd.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "vacancy_rate": [5.2, 4.8, 4.5],
                "geography": ["MSA001", "MSA001", "MSA001"],
            }
        )

        result = vacancy(df)
        assert isinstance(result, float)
        assert 4.0 <= result <= 6.0  # Reasonable range

    def test_vacancy_different_types(self):
        """Test vacancy calculation with different vacancy types."""
        hud_data = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, 4.8, 4.5],
            "geography": ["MSA001", "MSA001", "MSA001"],
        }

        # Test rental vacancy
        result_rental = vacancy(hud_data, vacancy_type="rental")
        assert result_rental > 0

        # Test multifamily vacancy
        result_multifamily = vacancy(hud_data, vacancy_type="multifamily")
        assert result_multifamily > 0

        # Test overall vacancy
        result_overall = vacancy(hud_data, vacancy_type="overall")
        assert result_overall > 0


class TestLeaseupCalculator:
    """Test cases for the lease-up time-on-market calculator."""

    def test_basic_leaseup_calculation(self):
        """Test basic lease-up time calculation."""
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=10, freq="D"),
            "property_id": ["PROP001"] * 5 + ["PROP002"] * 5,
            "days_on_market": [15, 20, 25, 18, 22, 12, 16, 19, 14, 17],
        }

        result = leaseup_tom(lease_data)

        # Should be median of all days_on_market values
        expected = 17.5  # Median of [12, 14, 15, 16, 17, 18, 19, 20, 22, 25]
        assert result == expected

    def test_leaseup_with_filters(self):
        """Test lease-up calculation with property filters."""
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=10, freq="D"),
            "property_id": ["PROP001"] * 5 + ["PROP002"] * 5,
            "property_type": ["apartment"] * 5 + ["condo"] * 5,
            "days_on_market": [15, 20, 25, 18, 22, 12, 16, 19, 14, 17],
        }

        # Filter to only apartments
        filters = {"property_type": "apartment"}
        result = leaseup_tom(lease_data, property_filters=filters)

        # Should be median of first 5 values: [15, 18, 20, 22, 25]
        expected = 20.0
        assert result == expected

    def test_leaseup_insufficient_data(self):
        """Test error handling for insufficient recent data."""
        lease_data = {
            "lease_date": pd.to_datetime(["2022-01-01"]),  # Old date
            "property_id": ["PROP001"],
            "days_on_market": [30],
        }

        with pytest.raises(ValueError, match="No lease data available"):
            leaseup_tom(lease_data, time_window_days=30)

    def test_leaseup_invalid_days(self):
        """Test error handling for invalid days on market."""
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=3, freq="D"),
            "property_id": ["PROP001", "PROP002", "PROP003"],
            "days_on_market": [15, -5, 25],  # Negative days
        }

        with pytest.raises(ValueError, match="between 0 and 365"):
            leaseup_tom(lease_data)

    def test_leaseup_no_valid_data(self):
        """Test error handling for no valid lease data."""
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=3, freq="D"),
            "property_id": ["PROP001", "PROP002", "PROP003"],
            "days_on_market": [np.nan, np.nan, np.nan],  # All NaN
        }

        with pytest.raises(ValueError, match="No valid days on market data"):
            leaseup_tom(lease_data)

    def test_leaseup_missing_columns(self):
        """Test error handling for missing required columns."""
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=3, freq="D"),
            "property_id": ["PROP001", "PROP002", "PROP003"],
            # Missing 'days_on_market' column
        }

        with pytest.raises(KeyError, match="Missing required columns"):
            leaseup_tom(lease_data)


class TestIntegration:
    """Integration tests for supply calculators."""

    def test_supply_calculator_integration(self):
        """Test integration of all supply calculators."""
        # This would test the integration of elasticity, vacancy, and lease-up
        # calculators in a realistic scenario
        pass

    def test_supply_calculator_pipeline(self):
        """Test the complete supply constraint calculation pipeline."""
        # This would test the flow from raw data to normalized scores
        pass
