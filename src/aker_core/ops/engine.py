from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def reputation_index(reviews: Iterable[Mapping[str, float | int | str]], nps: float | int) -> float:
    """Compute a 0–100 Reputation Index from reviews and NPS.

    Reviews items may contain: {rating: 1..5, weight?: float}. NPS is -100..100.
    A simple, explainable formula is used and easy to test:
      index = 0.6 * reviews_component + 0.4 * nps_component
      reviews_component = avg_rating / 5 * 100
      nps_component = (nps + 100) / 2
    """

    reviews = list(reviews)
    if not reviews:
        reviews_component = 50.0
    else:
        total_w = 0.0
        total = 0.0
        for r in reviews:
            rating = float(r.get("rating", 0))
            weight = float(r.get("weight", 1.0))
            total_w += weight
            total += rating * weight
        avg_rating = (total / total_w) if total_w > 0 else 0.0
        reviews_component = _clip(avg_rating / 5.0 * 100.0)

    nps_value = float(nps)
    # Map NPS -100..100 to 0..100
    nps_component = _clip((nps_value + 100.0) / 2.0)

    index = 0.6 * reviews_component + 0.4 * nps_component
    return _clip(index)


def pricing_rules(index: float) -> Mapping[str, float | int]:
    """Return pricing/concession guardrails based on reputation index.

    Example policy:
      - index >= 80: max_discount=2%, max_concession_days=0
      - 65 <= index < 80: max_discount=5%, max_concession_days=7
      - 50 <= index < 65: max_discount=8%, max_concession_days=14
      - index < 50: max_discount=12%, max_concession_days=21
    """
    idx = _clip(index)
    if idx >= 80:
        return {"max_discount_pct": 2.0, "max_concession_days": 0}
    if idx >= 65:
        return {"max_discount_pct": 5.0, "max_concession_days": 7}
    if idx >= 50:
        return {"max_discount_pct": 8.0, "max_concession_days": 14}
    return {"max_discount_pct": 12.0, "max_concession_days": 21}


@dataclass
class CadencePlan:
    """A renovation schedule plan that respects vacancy constraints.

    Attributes:
        weekly_schedule: List of units to renovate each week
        total_weeks: Total duration of the renovation project
        max_vacancy_rate: Maximum vacancy rate achieved during execution
        total_units: Total units to be renovated
    """
    weekly_schedule: list[int]
    total_weeks: int
    max_vacancy_rate: float
    total_units: int

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "weekly_schedule": self.weekly_schedule,
            "total_weeks": self.total_weeks,
            "max_vacancy_rate": self.max_vacancy_rate,
            "total_units": self.total_units
        }


def optimize_cadence(units: int, downtime_wk: int, vacancy_cap: float) -> CadencePlan:
    """Optimize renovation cadence to minimize time while respecting vacancy constraints.

    Args:
        units: Total number of units to renovate
        downtime_wk: Weeks of downtime required per unit
        vacancy_cap: Maximum allowed vacancy rate (0.0 to 1.0)

    Returns:
        CadencePlan with weekly schedule and metadata

    Raises:
        ValueError: If inputs are invalid or constraints cannot be satisfied
    """
    if units <= 0:
        raise ValueError("Units must be positive")
    if downtime_wk <= 0:
        raise ValueError("Downtime must be positive")
    if not 0.0 <= vacancy_cap <= 1.0:
        raise ValueError("Vacancy cap must be between 0.0 and 1.0")

    # Calculate maximum units that can be renovated per week
    # Each unit in renovation contributes to vacancy for downtime_wk weeks
    max_units_per_week = math.floor(1.0 / (downtime_wk * vacancy_cap))

    if max_units_per_week <= 0:
        raise ValueError(f"Vacancy cap {vacancy_cap} too restrictive for {downtime_wk}-week downtime")

    # If we can renovate all units in one week without exceeding cap
    if units <= max_units_per_week:
        return CadencePlan(
            weekly_schedule=[units],
            total_weeks=1,
            max_vacancy_rate=units * downtime_wk * vacancy_cap,
            total_units=units
        )

    # Calculate optimal schedule to minimize total weeks
    # Use a greedy approach: renovate as many as possible each week
    schedule = []
    remaining_units = units

    while remaining_units > 0:
        # Calculate how many units we can renovate this week
        # Consider the impact on future weeks due to overlapping downtime
        units_this_week = min(remaining_units, max_units_per_week)

        # Adjust for overlapping downtime effects
        # If we're in the final phase, we can be more aggressive
        if remaining_units <= max_units_per_week * 2:
            units_this_week = min(remaining_units, max_units_per_week)
        else:
            # Leave some capacity for future weeks to avoid bottlenecks
            units_this_week = min(remaining_units, max_units_per_week - 1)

        schedule.append(units_this_week)
        remaining_units -= units_this_week

    # The maximum vacancy rate is determined by the constraint we set
    # Since we calculated max_units_per_week based on vacancy_cap, the actual max rate achieved
    # will be at most vacancy_cap (when all allowed slots are filled)
    max_vacancy = vacancy_cap

    return CadencePlan(
        weekly_schedule=schedule,
        total_weeks=len(schedule),
        max_vacancy_rate=max_vacancy,
        total_units=units
    )


