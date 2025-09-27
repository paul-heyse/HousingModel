"""
Mathematical property tests for supply constraint calculators.

Tests the mathematical correctness of elasticity, vacancy, and lease-up calculations
including monotonicity, scaling invariance, and bounds guarantees.
"""

import pandas as pd

from aker_core.supply import elasticity, leaseup_tom, vacancy


class TestElasticityMathematicalProperties:
    """Test mathematical properties of elasticity calculations."""

    def test_monotonicity_preservation(self):
        """Test that elasticity preserves order (monotonicity)."""
        # Create two datasets where permits and households are ordered
        base_permits = [1000, 1100, 1200, 1300]
        base_households = [50000, 51000, 52000, 53000]

        # Create a second dataset with higher values
        higher_permits = [x + 100 for x in base_permits]
        higher_households = [x + 1000 for x in base_households]

        elasticity_base = elasticity(base_permits, base_households, years=3)
        elasticity_higher = elasticity(higher_permits, higher_households, years=3)

        # Higher inputs should produce higher elasticity
        assert elasticity_higher > elasticity_base

    def test_scaling_invariance(self):
        """Test that scaling inputs by a constant factor doesn't change results."""
        permits = [1000, 1100, 1200, 1300]
        households = [50000, 51000, 52000, 53000]

        # Calculate with original data
        elasticity_original = elasticity(permits, households, years=3)

        # Scale by constant factor
        scale_factor = 2.0
        scaled_permits = [x * scale_factor for x in permits]
        scaled_households = [x * scale_factor for x in households]

        elasticity_scaled = elasticity(scaled_permits, scaled_households, years=3)

        # Results should be identical (within numerical precision)
        assert abs(elasticity_original - elasticity_scaled) < 1e-10

    def test_bounds_guarantee(self):
        """Test that elasticity results are always non-negative."""
        # Test with various realistic datasets
        test_cases = [
            ([1000, 1100, 1200], [50000, 51000, 52000]),
            ([500, 600, 700], [25000, 26000, 27000]),
            ([2000, 2100, 2200], [100000, 101000, 102000]),
        ]

        for permits, households in test_cases:
            result = elasticity(permits, households, years=3)
            assert result >= 0, f"Elasticity should be non-negative, got {result}"

    def test_extreme_values_handling(self):
        """Test elasticity with extreme but valid values."""
        # Very small values
        small_permits = [1, 2, 3]
        small_households = [100, 101, 102]
        result_small = elasticity(small_permits, small_households, years=3)
        assert result_small >= 0

        # Very large values
        large_permits = [1000000, 1100000, 1200000]
        large_households = [50000000, 51000000, 52000000]
        result_large = elasticity(large_permits, large_households, years=3)
        assert result_large >= 0


class TestVacancyMathematicalProperties:
    """Test mathematical properties of vacancy calculations."""

    def test_reasonable_bounds(self):
        """Test that vacancy rates are within reasonable bounds."""
        test_cases = [
            {"year": [2020, 2021, 2022], "vacancy_rate": [5.2, 4.8, 4.5]},
            {"year": [2020, 2021, 2022], "vacancy_rate": [1.0, 1.2, 1.1]},
            {"year": [2020, 2021, 2022], "vacancy_rate": [15.0, 14.5, 14.8]},
        ]

        for hud_data in test_cases:
            result = vacancy(hud_data)
            assert 0 <= result <= 100, f"Vacancy rate should be 0-100%, got {result}"

    def test_consistency_with_different_formats(self):
        """Test that vacancy calculation is consistent across data formats."""
        hud_dict = {
            "year": [2020, 2021, 2022],
            "vacancy_rate": [5.2, 4.8, 4.5],
            "geography": ["MSA001", "MSA001", "MSA001"],
        }

        hud_df = pd.DataFrame(hud_dict)

        result_dict = vacancy(hud_dict)
        result_df = vacancy(hud_df)

        assert abs(result_dict - result_df) < 1e-10


class TestLeaseupMathematicalProperties:
    """Test mathematical properties of lease-up calculations."""

    def test_median_calculation_robustness(self):
        """Test that lease-up uses median (robust to outliers)."""
        # Create dataset with outliers
        lease_data = {
            "lease_date": pd.date_range("2023-01-01", periods=10, freq="D"),
            "days_on_market": [15, 20, 25, 18, 22, 12, 16, 19, 14, 100],  # 100 is outlier
        }

        result = leaseup_tom(lease_data)

        # Median should be robust to the 100-day outlier
        # Sorted: [12, 14, 15, 16, 18, 19, 20, 22, 25, 100]
        # Median should be average of 5th and 6th values: (18 + 19) / 2 = 18.5
        expected = 18.5
        assert abs(result - expected) < 0.1

    def test_time_window_filtering(self):
        """Test that lease-up correctly filters by time window."""
        base_date = pd.Timestamp("2023-01-15")

        # Create data with some old and some recent leases
        lease_data = {
            "lease_date": [
                base_date - pd.Timedelta(days=100),  # Old
                base_date - pd.Timedelta(days=50),  # Old
                base_date - pd.Timedelta(days=10),  # Recent
                base_date - pd.Timedelta(days=5),  # Recent
            ],
            "days_on_market": [30, 25, 15, 20],
        }

        # Should only include leases within 30 days
        result = leaseup_tom(lease_data, time_window_days=30)

        # Should only have 2 recent leases with days [15, 20]
        # Median should be 17.5
        expected = 17.5
        assert abs(result - expected) < 0.1


class TestInverseScoringProperties:
    """Test the inverse scoring logic for supply constraints."""

    def test_elasticity_inverse_relationship(self):
        """Test that higher elasticity produces lower constraint scores."""
        from aker_core.supply import inverse_elasticity_score

        # Higher elasticity should produce lower constraint score
        high_elasticity = 50.0  # Very supply-responsive
        low_elasticity = 10.0  # Less supply-responsive

        high_score = inverse_elasticity_score(high_elasticity)
        low_score = inverse_elasticity_score(low_elasticity)

        # Higher elasticity should produce lower constraint score
        assert high_score < low_score

        # Both should be in valid range
        assert 0 <= high_score <= 100
        assert 0 <= low_score <= 100

    def test_vacancy_inverse_relationship(self):
        """Test that lower vacancy produces higher constraint scores."""
        from aker_core.supply import inverse_vacancy_score

        # Lower vacancy should produce higher constraint score
        low_vacancy = 2.0  # Very tight market
        high_vacancy = 10.0  # More supply available

        low_score = inverse_vacancy_score(low_vacancy)
        high_score = inverse_vacancy_score(high_vacancy)

        # Lower vacancy should produce higher constraint score
        assert low_score > high_score

        # Both should be in valid range
        assert 0 <= low_score <= 100
        assert 0 <= high_score <= 100

    def test_leaseup_inverse_relationship(self):
        """Test that shorter lease-up times produce higher constraint scores."""
        from aker_core.supply import inverse_leaseup_score

        # Shorter lease-up should produce higher constraint score
        short_leaseup = 10.0  # Very fast lease-up
        long_leaseup = 60.0  # Slower lease-up

        short_score = inverse_leaseup_score(short_leaseup)
        long_score = inverse_leaseup_score(long_leaseup)

        # Shorter lease-up should produce higher constraint score
        assert short_score > long_score

        # Both should be in valid range
        assert 0 <= short_score <= 100
        assert 0 <= long_score <= 100


class TestIntegrationProperties:
    """Test integration of all supply calculators."""

    def test_end_to_end_supply_calculation(self):
        """Test complete supply calculation pipeline."""
        # This would test the integration of all three calculators
        # in a realistic scenario
        pass

    def test_supply_score_composition(self):
        """Test that supply scores can be properly composed."""
        # This would test the integration with pillar scoring
        pass
