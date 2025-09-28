from __future__ import annotations

from math import inf
from typing import List, Sequence

from .types import RankConfig, RankedScope, ScopeTemplate


def _evaluate_scope(scope: ScopeTemplate, config: RankConfig) -> RankedScope:
    cost: float = scope.cost
    annual_savings: float = scope.annual_savings
    downtime_cost: float = scope.downtime_hours * scope.downtime_cost_rate_per_hour

    reasons: List[str] = []

    if cost <= 0.0:
        reasons.append("non-positive cost")

    net_savings: float = annual_savings - downtime_cost
    if net_savings <= 0.0:
        reasons.append("non-positive net savings")

    roi: float = (net_savings / cost) if cost > 0.0 and net_savings > 0.0 else 0.0
    payback_years: float = (cost / net_savings) if net_savings > 0.0 else inf

    if roi < config.min_roi:
        reasons.append("below min ROI")
    if payback_years > config.max_payback_years:
        reasons.append("exceeds max payback")

    viable: bool = not reasons

    return RankedScope(
        name=scope.name,
        roi=roi,
        payback_years=payback_years,
        downtime_hours=scope.downtime_hours,
        cost=cost,
        viable=viable,
        reasons=tuple(reasons),
    )


def rank_scopes(
    asset_id: str,
    scopes: Sequence[ScopeTemplate],
    *,
    config: RankConfig | None = None,
) -> List[RankedScope]:
    """Compute ROI/payback for scopes and return viable scopes ranked by ROI.

    Ordering: ROI desc, downtime ascending, cost ascending.
    Scopes that do not meet thresholds are excluded.
    """
    cfg: RankConfig = config if config is not None else RankConfig()

    evaluated: List[RankedScope] = [_evaluate_scope(s, cfg) for s in scopes]
    viable_scopes: List[RankedScope] = [s for s in evaluated if s.viable]

    viable_scopes.sort(
        key=lambda s: (
            -s.roi,
            s.downtime_hours,
            s.cost,
        )
    )
    return viable_scopes


