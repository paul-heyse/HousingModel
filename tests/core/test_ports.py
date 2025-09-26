from __future__ import annotations

from typing import Mapping

from aker_core.ports import AssetEvaluator, DealArchetypeModel, MarketScorer, RiskEngine


class MarketStub:
    def score_market(self, *, market: Mapping[str, str]):
        return {"score": 1}


class AssetStub:
    def evaluate_asset(self, *, asset: Mapping[str, str]):
        return {"fit": True}


class DealStub:
    def model_deal(self, *, deal: Mapping[str, str]):
        return {"irr": 0.12}


class RiskStub:
    def assess_risk(self, *, context: Mapping[str, str]):
        return {"risk": "low"}


def test_port_protocols_accept_stubs():
    market_stub = MarketStub()
    asset_stub = AssetStub()
    deal_stub = DealStub()
    risk_stub = RiskStub()

    assert isinstance(market_stub, MarketScorer)
    assert isinstance(asset_stub, AssetEvaluator)
    assert isinstance(deal_stub, DealArchetypeModel)
    assert isinstance(risk_stub, RiskEngine)
