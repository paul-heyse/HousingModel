from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class AssetAttributes:
    asset_id: int
    msa_id: str
    product_type: Optional[str]
    year_built: Optional[int]
    unit_mix: Optional[list]
    ceiling_min_ft: Optional[float]
    wd_in_unit: Optional[bool]
    parking_ratio: Optional[float]


class AssetAttributesConnector:
    def fetch(self, *, asset_id: int) -> AssetAttributes:
        raise NotImplementedError


@dataclass(frozen=True)
class ContextEnrichment:
    label: Optional[str]
    allowed_product_types: List[str]
    min_year_built: Optional[int]
    min_unit_size: Mapping[str, float]
    min_ceiling_ft: Optional[float]
    require_wd_in_unit: bool
    parking_ratio_required: Optional[float]


class ContextConnector:
    def infer(self, *, msa_id: str, asset_point: Optional[object] = None) -> ContextEnrichment:
        raise NotImplementedError


@dataclass(frozen=True)
class RegulatoryRule:
    code: str
    payload: Mapping[str, object]


class RegulatoryRulesConnector:
    def rules_for(self, *, msa_id: str) -> Iterable[RegulatoryRule]:
        raise NotImplementedError


@dataclass(frozen=True)
class MarketComps:
    size_reference_by_type: Mapping[str, float]


class MarketCompsConnector:
    def fetch(self, *, msa_id: str, product_type: Optional[str]) -> MarketComps:
        raise NotImplementedError
