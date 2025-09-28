"""Integration tests for ops module with database and asset data."""

from aker_core.ops import optimize_cadence


class TestOpsIntegration:
    """Integration tests for operations module."""

    def test_optimize_cadence_with_realistic_asset_scenario(self):
        """Test optimization with realistic asset parameters."""
        # Simulate a 150-unit apartment building
        # 3-week renovation downtime per unit
        # 7% maximum vacancy allowed
        plan = optimize_cadence(units=150, downtime_wk=3, vacancy_cap=0.07)

        assert plan.total_units == 150
        assert sum(plan.weekly_schedule) == 150
        assert plan.total_weeks > 1  # Should take multiple weeks

        # With 7% cap and 3-week downtime, max units/week = floor(1/(3*0.07)) = 4
        assert all(week <= 4 for week in plan.weekly_schedule)

        # Should complete within reasonable timeframe
        assert plan.total_weeks <= 40  # 150 units / 4 units/week = 37.5 weeks

    def test_cadence_plan_database_persistence(self):
        """Test that cadence plans can be stored in database."""
        plan = optimize_cadence(units=50, downtime_wk=2, vacancy_cap=0.1)

        # Convert to dict for database storage (as JSON string)
        plan_dict = plan.to_dict()

        # Verify the structure matches what database expects
        assert "weekly_schedule" in plan_dict
        assert "total_weeks" in plan_dict
        assert "max_vacancy_rate" in plan_dict
        assert "total_units" in plan_dict

        assert isinstance(plan_dict["weekly_schedule"], list)
        assert isinstance(plan_dict["total_weeks"], int)
        assert isinstance(plan_dict["max_vacancy_rate"], float)
        assert isinstance(plan_dict["total_units"], int)

    def test_multiple_asset_portfolio_optimization(self):
        """Test optimizing cadence across multiple assets."""
        assets = [
            {"units": 80, "downtime_wk": 2, "vacancy_cap": 0.08},  # Large building
            {"units": 40, "downtime_wk": 3, "vacancy_cap": 0.06},  # Medium building
            {"units": 20, "downtime_wk": 1, "vacancy_cap": 0.12},  # Small building
        ]

        # Test individual optimizations
        plans = []
        for asset in assets:
            plan = optimize_cadence(**asset)
            plans.append(plan)
            assert plan.total_units == asset["units"]
            assert sum(plan.weekly_schedule) == asset["units"]

        # Verify all plans respect their individual constraints
        for plan, asset in zip(plans, assets):
            assert all(week <= asset["units"] for week in plan.weekly_schedule)

        total_units = sum(asset["units"] for asset in assets)
        assert sum(plan.total_units for plan in plans) == total_units

    def test_cadence_plan_edge_cases(self):
        """Test edge cases that might occur in real operations."""
        # Very large building
        plan = optimize_cadence(units=500, downtime_wk=4, vacancy_cap=0.05)
        assert plan.total_units == 500
        assert plan.total_weeks > 10  # Should take significant time

        # Very small downtime (1 week)
        plan = optimize_cadence(units=10, downtime_wk=1, vacancy_cap=0.5)
        assert plan.total_weeks == 1  # Should complete in one week
        assert plan.weekly_schedule == [10]

        # Very restrictive vacancy cap
        plan = optimize_cadence(units=20, downtime_wk=2, vacancy_cap=0.02)
        assert all(week <= 25 for week in plan.weekly_schedule)  # floor(1/(2*0.02)) = 25

    def test_cadence_plan_calculations(self):
        """Test that vacancy rate calculations are correct."""
        plan = optimize_cadence(units=8, downtime_wk=2, vacancy_cap=0.1)

        # With 10% cap and 2-week downtime, max units/week should be floor(1/(2*0.1)) = 5
        assert all(week <= 5 for week in plan.weekly_schedule)

        # Total units should match
        assert sum(plan.weekly_schedule) == 8

        # Max vacancy should be <= 20% (2 weeks * 10% cap)
        assert plan.max_vacancy_rate <= 0.2
