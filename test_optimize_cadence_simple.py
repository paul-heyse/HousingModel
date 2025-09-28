#!/usr/bin/env python3
"""Simple test script for optimize_cadence function."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from aker_core.ops import optimize_cadence

    def test_basic():
        print("Testing basic single-week case...")
        plan = optimize_cadence(units=5, downtime_wk=2, vacancy_cap=0.1)
        assert plan.total_units == 5
        assert plan.total_weeks == 1
        assert plan.weekly_schedule == [5]
        print("✓ Basic test passed")

    def test_multi_week():
        print("Testing multi-week case...")
        plan = optimize_cadence(units=20, downtime_wk=2, vacancy_cap=0.1)
        assert plan.total_units == 20
        assert plan.total_weeks > 1
        assert sum(plan.weekly_schedule) == 20
        print("✓ Multi-week test passed")

    def test_constraint():
        print("Testing vacancy constraint...")
        plan = optimize_cadence(units=10, downtime_wk=3, vacancy_cap=0.05)
        # With 5% cap and 3-week downtime, max units/week should be floor(1/(3*0.05)) = 6
        assert all(week <= 6 for week in plan.weekly_schedule)
        print("✓ Constraint test passed")

    def test_serialization():
        print("Testing serialization...")
        plan = optimize_cadence(units=8, downtime_wk=2, vacancy_cap=0.1)
        data = plan.to_dict()
        assert data["total_units"] == 8
        assert sum(data["weekly_schedule"]) == 8
        print("✓ Serialization test passed")

    def test_realistic():
        print("Testing realistic scenario...")
        plan = optimize_cadence(units=100, downtime_wk=2, vacancy_cap=0.08)
        assert plan.total_units == 100
        assert sum(plan.weekly_schedule) == 100
        assert plan.total_weeks <= 25  # Should complete in reasonable time
        print("✓ Realistic scenario test passed")

    if __name__ == "__main__":
        print("Running optimize_cadence tests...")
        test_basic()
        test_multi_week()
        test_constraint()
        test_serialization()
        test_realistic()
        print("\n🎉 All tests passed!")

except Exception as exc:  # pragma: no cover - manual script
    import traceback

    print(f"❌ Test failed: {exc}")
    traceback.print_exc()
    sys.exit(1)
