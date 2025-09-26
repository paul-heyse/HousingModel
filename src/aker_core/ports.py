"""Port contracts for the Aker plugin architecture."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class MarketScorer(Protocol):
    """Scores markets given a payload of metrics and returns scoring outputs."""

    def score_market(self, *, market: Mapping[str, Any]) -> Mapping[str, Any]:
        """Compute scores for the provided market input."""


@runtime_checkable
class AssetEvaluator(Protocol):
    """Evaluates asset fundamentals and returns guardrail assessments."""

    def evaluate_asset(self, *, asset: Mapping[str, Any]) -> Mapping[str, Any]:
        """Evaluate a single asset and return structured metrics."""


@runtime_checkable
class DealArchetypeModel(Protocol):
    """Models deal archetypes and returns scenario economics."""

    def model_deal(self, *, deal: Mapping[str, Any]) -> Mapping[str, Any]:
        """Model the deal and return computed economics."""


@runtime_checkable
class RiskEngine(Protocol):
    """Assesses risk and resilience signals for a given context."""

    def assess_risk(self, *, context: Mapping[str, Any]) -> Mapping[str, Any]:
        """Assess risk for the provided context."""


__all__ = [
    "MarketScorer",
    "AssetEvaluator",
    "DealArchetypeModel",
    "RiskEngine",
]
