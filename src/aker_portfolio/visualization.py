"""
Dashboard visualization components for portfolio exposure monitoring.

This module provides data structures and utilities for creating dashboard
visualizations of portfolio exposures, alerts, and trends.
"""

from __future__ import annotations

from typing import Optional

from .types import ExposureDimension, ExposureResult, PortfolioAlert


class ExposureVisualization:
    """Data structures for exposure dashboard visualizations."""

    def __init__(self, exposure_result: ExposureResult):
        self.exposure_result = exposure_result
        self.total_value = exposure_result.total_portfolio_value
        self.as_of_date = exposure_result.as_of_date

    def get_exposure_dials_data(self) -> list[dict]:
        """Get data formatted for exposure dial charts."""
        dials = []

        # Strategy exposure dial
        strategy_exposures = self._get_dimension_exposures("strategy")
        if strategy_exposures:
            dials.append({
                "type": "strategy",
                "title": "Strategy Exposure",
                "data": [
                    {
                        "label": exp.dimension_value.title(),
                        "value": exp.exposure_pct,
                        "color": self._get_strategy_color(exp.dimension_value)
                    }
                    for exp in strategy_exposures
                ]
            })

        # Geographic exposure dial
        geo_exposures = self._get_dimension_exposures("state")
        if geo_exposures:
            dials.append({
                "type": "geographic",
                "title": "Geographic Exposure",
                "data": [
                    {
                        "label": exp.dimension_value.upper(),
                        "value": exp.exposure_pct,
                        "color": self._get_state_color(exp.dimension_value)
                    }
                    for exp in geo_exposures
                ]
            })

        return dials

    def get_exposure_chart_data(self) -> dict:
        """Get data formatted for exposure trend charts."""
        return {
            "labels": ["Strategy", "State", "MSA", "Vintage", "Construction", "Rent Band"],
            "datasets": [
                {
                    "label": "Exposure %",
                    "data": [
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("strategy")),
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("state")),
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("msa")),
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("vintage")),
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("construction_type")),
                        sum(exp.exposure_pct for exp in self._get_dimension_exposures("rent_band")),
                    ],
                    "backgroundColor": [
                        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"
                    ]
                }
            ]
        }

    def get_alert_summary_data(self, alerts: list[PortfolioAlert]) -> dict:
        """Get data formatted for alert summary dashboard."""
        active_alerts = [alert for alert in alerts if alert.status == "active"]

        return {
            "total_alerts": len(alerts),
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in active_alerts if a.severity == "warning"]),
            "recent_alerts": [
                {
                    "message": alert.alert_message,
                    "severity": alert.severity,
                    "dimension": alert.exposure_id.split("_")[0],
                    "value": alert.exposure_id.split("_")[1],
                    "created_at": alert.created_at.isoformat() if alert.created_at else None
                }
                for alert in alerts[-5:]  # Last 5 alerts
            ]
        }

    def _get_dimension_exposures(self, dimension_type: str) -> list[ExposureDimension]:
        """Get exposures for a specific dimension type."""
        return [
            exp for exp in self.exposure_result.exposures
            if exp.dimension_type == dimension_type
        ]

    def _get_strategy_color(self, strategy: str) -> str:
        """Get color for strategy visualization."""
        colors = {
            "core": "#4BC0C0",
            "core_plus": "#36A2EB",
            "value_add": "#FF6384",
            "opportunistic": "#FF9F40",
            "development": "#9966FF",
        }
        return colors.get(strategy.lower(), "#CCCCCC")

    def _get_state_color(self, state: str) -> str:
        """Get color for state visualization."""
        # Simple color mapping - could be expanded
        colors = {
            "CA": "#FF6384",
            "TX": "#36A2EB",
            "FL": "#FFCE56",
            "NY": "#4BC0C0",
            "WA": "#9966FF",
        }
        return colors.get(state.upper(), "#CCCCCC")


class ExposureTrendAnalyzer:
    """Analyze exposure trends over time."""

    def __init__(self, historical_exposures: list[ExposureResult]):
        self.historical_exposures = historical_exposures

    def get_trend_data(self, dimension_type: str, dimension_value: Optional[str] = None) -> dict:
        """Get trend data for a specific dimension."""
        trend_data = []

        for exposure_result in sorted(self.historical_exposures, key=lambda x: x.as_of_date):
            if dimension_value:
                matching_exposures = [
                    exp for exp in exposure_result.exposures
                    if exp.dimension_type == dimension_type and exp.dimension_value == dimension_value
                ]
            else:
                matching_exposures = [
                    exp for exp in exposure_result.exposures
                    if exp.dimension_type == dimension_type
                ]

            if matching_exposures:
                total_pct = sum(exp.exposure_pct for exp in matching_exposures)
                trend_data.append({
                    "date": exposure_result.as_of_date.isoformat(),
                    "value": total_pct,
                    "portfolio_value": exposure_result.total_portfolio_value
                })

        return {
            "dimension_type": dimension_type,
            "dimension_value": dimension_value,
            "trend_data": trend_data,
            "current_value": trend_data[-1]["value"] if trend_data else 0,
            "change_from_baseline": self._calculate_change_from_baseline(trend_data)
        }

    def _calculate_change_from_baseline(self, trend_data: list[dict]) -> float:
        """Calculate percentage change from baseline."""
        if len(trend_data) < 2:
            return 0.0

        baseline = trend_data[0]["value"]
        current = trend_data[-1]["value"]

        if baseline == 0:
            return 0.0

        return ((current - baseline) / baseline) * 100


class ExposureComparisonTool:
    """Tools for comparing current vs target/limit exposures."""

    def __init__(self, current_exposures: ExposureResult):
        self.current_exposures = current_exposures

    def compare_to_limits(self, limits: dict[str, float]) -> list[dict]:
        """Compare current exposures to configured limits."""
        comparisons = []

        for dimension_type, limit_pct in limits.items():
            current_exposures = self._get_dimension_exposures(dimension_type)
            current_total = sum(exp.exposure_pct for exp in current_exposures)

            comparisons.append({
                "dimension_type": dimension_type,
                "current_pct": current_total,
                "limit_pct": limit_pct,
                "breach_pct": max(0, current_total - limit_pct),
                "status": "breach" if current_total > limit_pct else "within_limit",
                "dimension_breakdown": [
                    {
                        "value": exp.dimension_value,
                        "current_pct": exp.exposure_pct,
                        "contribution_to_breach": max(0, exp.exposure_pct - (limit_pct * exp.exposure_pct / current_total)) if current_total > 0 else 0
                    }
                    for exp in current_exposures
                ]
            })

        return comparisons

    def _get_dimension_exposures(self, dimension_type: str) -> list[ExposureDimension]:
        """Get exposures for a specific dimension type."""
        return [
            exp for exp in self.current_exposures.exposures
            if exp.dimension_type == dimension_type
        ]
