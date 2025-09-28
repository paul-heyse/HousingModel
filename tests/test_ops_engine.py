from __future__ import annotations

import pytest

from aker_core.ops import optimize_cadence, pricing_rules, reputation_index


def test_reputation_index_deterministic():
    reviews = [{"rating": 4.0}, {"rating": 5.0}]
    nps = 20
    idx1 = reputation_index(reviews, nps)
    idx2 = reputation_index(reviews, nps)
    assert idx1 == idx2
    assert 0 <= idx1 <= 100


def test_pricing_rules_monotonicity():
    rules_low = pricing_rules(45)
    rules_mid = pricing_rules(70)
    rules_high = pricing_rules(85)
    assert rules_high["max_discount_pct"] <= rules_mid["max_discount_pct"] <= rules_low["max_discount_pct"]
    assert rules_high["max_concession_days"] <= rules_mid["max_concession_days"] <= rules_low["max_concession_days"]


# Tests for optimize_cadence function

def test_optimize_cadence_basic_single_week():
    """Test basic case where all units can be renovated in one week."""
    plan = optimize_cadence(units=5, downtime_wk=2, vacancy_cap=0.1)

    assert plan.total_units == 5
    assert plan.total_weeks == 1
    assert plan.weekly_schedule == [5]
    assert plan.max_vacancy_rate <= 1.0  # Should not exceed 100% vacancy


def test_optimize_cadence_multi_week():
    """Test case requiring multiple weeks."""
    plan = optimize_cadence(units=20, downtime_wk=2, vacancy_cap=0.1)

    assert plan.total_units == 20
    assert plan.total_weeks > 1
    assert sum(plan.weekly_schedule) == 20
    assert all(week > 0 for week in plan.weekly_schedule)
    assert plan.max_vacancy_rate <= 1.0


def test_optimize_cadence_vacancy_constraint_respected():
    """Test that vacancy cap is never exceeded."""
    plan = optimize_cadence(units=10, downtime_wk=3, vacancy_cap=0.05)  # 5% cap

    # Each unit contributes to vacancy for 3 weeks, so max per week should be floor(1/(3*0.05)) = 6
    assert all(week <= 6 for week in plan.weekly_schedule)
    assert plan.max_vacancy_rate <= 0.05 * 3  # Max 15% effective vacancy


def test_optimize_cadence_input_validation():
    """Test input validation."""
    with pytest.raises(ValueError, match="Units must be positive"):
        optimize_cadence(units=0, downtime_wk=2, vacancy_cap=0.1)

    with pytest.raises(ValueError, match="Downtime must be positive"):
        optimize_cadence(units=10, downtime_wk=0, vacancy_cap=0.1)

    with pytest.raises(ValueError, match="Vacancy cap must be between 0.0 and 1.0"):
        optimize_cadence(units=10, downtime_wk=2, vacancy_cap=1.5)

    with pytest.raises(ValueError, match="Vacancy cap .* too restrictive"):
        optimize_cadence(units=10, downtime_wk=2, vacancy_cap=0.01)  # Too restrictive


def test_optimize_cadence_deterministic():
    """Test that results are deterministic."""
    plan1 = optimize_cadence(units=15, downtime_wk=2, vacancy_cap=0.1)
    plan2 = optimize_cadence(units=15, downtime_wk=2, vacancy_cap=0.1)

    assert plan1.weekly_schedule == plan2.weekly_schedule
    assert plan1.total_weeks == plan2.total_weeks
    assert plan1.max_vacancy_rate == plan2.max_vacancy_rate


def test_optimize_cadence_edge_case_small_units():
    """Test edge case with very few units."""
    plan = optimize_cadence(units=1, downtime_wk=1, vacancy_cap=0.5)

    assert plan.total_units == 1
    assert plan.total_weeks == 1
    assert plan.weekly_schedule == [1]
    assert plan.max_vacancy_rate <= 0.5


def test_optimize_cadence_edge_case_max_constraint():
    """Test case where constraint is at maximum capacity."""
    plan = optimize_cadence(units=10, downtime_wk=1, vacancy_cap=1.0)

    assert plan.total_units == 10
    assert plan.weekly_schedule == [10]  # All in one week
    assert plan.max_vacancy_rate <= 1.0


def test_cadence_plan_to_dict():
    """Test CadencePlan serialization."""
    plan = optimize_cadence(units=8, downtime_wk=2, vacancy_cap=0.1)
    data = plan.to_dict()

    assert data["total_units"] == 8
    assert data["total_weeks"] == len(data["weekly_schedule"])
    assert data["weekly_schedule"] == plan.weekly_schedule
    assert data["max_vacancy_rate"] == plan.max_vacancy_rate
    assert sum(data["weekly_schedule"]) == 8


def test_optimize_cadence_realistic_scenario():
    """Test with realistic property management scenario."""
    # 100-unit building, 2-week downtime per unit, 8% vacancy cap
    plan = optimize_cadence(units=100, downtime_wk=2, vacancy_cap=0.08)

    assert plan.total_units == 100
    assert sum(plan.weekly_schedule) == 100
    assert plan.max_vacancy_rate <= 0.08 * 2  # Max 16% effective vacancy

    # Should complete in reasonable time (not more than ~25 weeks with 4 units/week max)
    assert plan.total_weeks <= 25


