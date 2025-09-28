from __future__ import annotations

from aker_deal import RankConfig, ScopeTemplate, rank_scopes


def test_rank_scopes_orders_by_roi_and_tiebreaks() -> None:
    scopes = [
        ScopeTemplate(name="A", cost=1000, annual_savings=400, downtime_hours=5, downtime_cost_rate_per_hour=10),
        ScopeTemplate(name="B", cost=1000, annual_savings=400, downtime_hours=2, downtime_cost_rate_per_hour=10),
        ScopeTemplate(name="C", cost=800, annual_savings=300, downtime_hours=2, downtime_cost_rate_per_hour=10),
    ]

    ranked = rank_scopes("asset-1", scopes)

    # Compute ROIs to determine expected order
    # A: net=400-50=350 → ROI=0.35
    # B: net=400-20=380 → ROI=0.38
    # C: net=300-20=280 → ROI=0.35, cost smaller than A but ROI lower than B
    names = [s.name for s in ranked]
    assert names == ["B", "C", "A"]


def test_payback_guard_excludes_long_payback() -> None:
    scopes = [
        ScopeTemplate(name="Slow", cost=1000, annual_savings=50),  # payback = 20 yrs
        ScopeTemplate(name="Fast", cost=1000, annual_savings=400),  # payback = 2.5 yrs
    ]

    ranked = rank_scopes("asset-1", scopes, config=RankConfig(max_payback_years=5.0))
    names = [s.name for s in ranked]
    assert names == ["Fast"]


def test_min_roi_threshold_filters() -> None:
    scopes = [
        ScopeTemplate(name="LowROI", cost=1000, annual_savings=10),  # roi ~ 0.01
        ScopeTemplate(name="OK", cost=1000, annual_savings=300),  # roi ~ 0.30
    ]

    ranked = rank_scopes("asset-1", scopes, config=RankConfig(min_roi=0.1))
    names = [s.name for s in ranked]
    assert names == ["OK"]


