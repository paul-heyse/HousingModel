from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Tuple


@dataclass(frozen=True)
class ScopeTemplate:
    """Deal scope archetype capturing costs, expected savings, and downtime parameters."""

    name: str
    cost: float
    annual_savings: float
    downtime_hours: float = 0.0
    downtime_cost_rate_per_hour: float = 0.0
    lifetime_years: float = 0.0
    tags: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RankedScope:
    name: str
    roi: float
    payback_years: float
    downtime_hours: float
    cost: float
    viable: bool
    reasons: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RankConfig:
    """Thresholds and knobs for scope ranking."""

    min_roi: float = 0.0
    max_payback_years: float = 10.0


def deal_archetype(
    *,
    name: str,
    cost: float,
    annual_savings: float,
    downtime_hours: float = 0.0,
    downtime_cost_rate_per_hour: float = 0.0,
    lifetime_years: float = 0.0,
    tags: Sequence[str] | None = None,
) -> ScopeTemplate:
    """Factory for creating a :class:`ScopeTemplate`.

    Provided to match the OpenSpec surface described as ``deal_archetype(...)``.
    """
    return ScopeTemplate(
        name=name,
        cost=float(cost),
        annual_savings=float(annual_savings),
        downtime_hours=float(downtime_hours),
        downtime_cost_rate_per_hour=float(downtime_cost_rate_per_hour),
        lifetime_years=float(lifetime_years),
        tags=tuple(tags) if tags else tuple(),
    )


