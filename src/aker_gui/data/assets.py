"""Fixture-backed data helpers for GUI prototypes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


_ASSET_FIXTURES: Dict[str, Dict[str, Any]] = {
    "AKR-123": {
        "asset_id": "AKR-123",
        "name": "Maple Grove Residences",
        "msa_id": "BOI",
        "product_type": "garden",
        "year_built": 2015,
        "total_units": 120,
        "unit_mix": [
            {"type": "studio", "pct": 10.0, "size_sqft": 480},
            {"type": "1br", "pct": 55.0, "size_sqft": 690},
            {"type": "2br", "pct": 35.0, "size_sqft": 960},
        ],
        "ceiling_min_ft": 9.0,
        "wd_in_unit": True,
        "parking_ratio": 1.1,
        "parking_context": "surface",
        "amenities": {
            "balconies": True,
            "gear_nook": False,
            "bike_storage": True,
            "dog_wash": False,
            "ev_ready": False,
        },
    },
    "AKR-456": {
        "asset_id": "AKR-456",
        "name": "Union Station Lofts",
        "msa_id": "DEN",
        "product_type": "mid_rise",
        "year_built": 2008,
        "total_units": 210,
        "unit_mix": [
            {"type": "studio", "pct": 20.0, "size_sqft": 520},
            {"type": "1br", "pct": 50.0, "size_sqft": 720},
            {"type": "2br", "pct": 30.0, "size_sqft": 980},
        ],
        "ceiling_min_ft": 9.5,
        "wd_in_unit": True,
        "parking_ratio": 1.25,
        "parking_context": "structured",
        "amenities": {
            "balconies": True,
            "gear_nook": True,
            "bike_storage": True,
            "dog_wash": True,
            "ev_ready": True,
        },
    },
}


_GUARDRAIL_SETS: Dict[str, Dict[str, Any]] = {
    "BOI": {
        "label": "Mountain West Secondary",
        "allowed_product_types": ["garden", "mid_rise", "mixed_use"],
        "min_year_built": 2010,
        "min_unit_size": {"studio": 450, "1br": 650, "2br": 900},
        "min_ceiling_ft": 8.5,
        "require_wd_in_unit": True,
        "parking_ratio_required": 1.1,
        "product_defaults": {
            "garden": {
                "ceiling_min_ft": 9.0,
                "parking_ratio": 1.15,
                "amenities": {
                    "balconies": True,
                    "bike_storage": True,
                    "dog_wash": False,
                    "ev_ready": False,
                },
            }
        },
    },
    "DEN": {
        "label": "Tier 1 Urban",
        "allowed_product_types": ["mid_rise", "mixed_use", "tower"],
        "min_year_built": 2005,
        "min_unit_size": {"studio": 480, "1br": 700, "2br": 950},
        "min_ceiling_ft": 9.0,
        "require_wd_in_unit": True,
        "parking_ratio_required": 1.0,
        "product_defaults": {
            "mid_rise": {
                "ceiling_min_ft": 9.5,
                "parking_ratio": 1.2,
                "amenities": {
                    "balconies": True,
                    "bike_storage": True,
                    "dog_wash": True,
                    "ev_ready": True,
                },
            }
        },
    },
}


def list_assets() -> List[Dict[str, Any]]:
    """Return all fixture assets."""

    return [deepcopy(asset) for asset in _ASSET_FIXTURES.values()]


def get_asset(asset_id: str) -> Optional[Dict[str, Any]]:
    """Return a single asset fixture if available."""

    record = _ASSET_FIXTURES.get(asset_id)
    return deepcopy(record) if record else None


def get_guardrails(msa_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return guardrail configuration for an MSA."""

    if msa_id is None:
        return None
    config = _GUARDRAIL_SETS.get(msa_id.upper())
    return deepcopy(config) if config else None


def get_default_form_inputs(asset_id: str) -> Dict[str, Any]:
    """Return default wizard inputs for an asset."""

    asset = get_asset(asset_id) or {}
    return {
        "asset_id": asset.get("asset_id", asset_id),
        "name": asset.get("name"),
        "msa_id": asset.get("msa_id"),
        "product_type": asset.get("product_type"),
        "year_built": asset.get("year_built"),
        "total_units": asset.get("total_units"),
        "unit_mix": deepcopy(asset.get("unit_mix", [])),
        "ceiling_min_ft": asset.get("ceiling_min_ft"),
        "wd_in_unit": bool(asset.get("wd_in_unit", False)),
        "parking_ratio_observed": asset.get("parking_ratio"),
        "parking_context": asset.get("parking_context", "surface"),
        "amenities": deepcopy(asset.get("amenities", {})),
    }


def get_product_default(asset_id: str, product_type: Optional[str]) -> Optional[Dict[str, Any]]:
    asset = get_asset(asset_id)
    msa_id = asset.get("msa_id") if asset else None
    guardrails = get_guardrails(msa_id) if msa_id else None
    if not guardrails:
        return None
    defaults = guardrails.get("product_defaults", {})
    if product_type and product_type in defaults:
        return deepcopy(defaults[product_type])
    return None

