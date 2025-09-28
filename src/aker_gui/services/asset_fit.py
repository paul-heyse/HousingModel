"""Shared helpers for evaluating asset fit within the GUI."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional

from aker_core.asset import fit as core_fit


def normalise_unit_mix(unit_mix: Optional[Iterable[Mapping[str, Any]]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    if not unit_mix:
        return output
    for item in unit_mix:
        output.append(
            {
                "type": item.get("type"),
                "pct": item.get("pct"),
                "size_sqft": item.get("size_sqft") or item.get("size"),
            }
        )
    return output


def build_asset_payload(defaults: Mapping[str, Any], inputs: Mapping[str, Any]) -> Dict[str, Any]:
    amenities_default = defaults.get("amenities", {})

    def bool_value(key: str) -> bool:
        if key in inputs and inputs[key] is not None:
            return bool(inputs[key])
        return bool(amenities_default.get(key, False))

    return {
        "product_type": inputs.get("product_type", defaults.get("product_type")),
        "year_built": inputs.get("year_built", defaults.get("year_built")),
        "unit_mix": normalise_unit_mix(inputs.get("unit_mix") or defaults.get("unit_mix")),
        "ceiling_min_ft": inputs.get("ceiling_min_ft", defaults.get("ceiling_min_ft")),
        "wd_in_unit": bool(inputs.get("wd_in_unit", defaults.get("wd_in_unit", False))),
        "parking_ratio": inputs.get(
            "parking_ratio_observed",
            defaults.get("parking_ratio_observed", defaults.get("parking_ratio")),
        ),
        "amenities": {
            "balconies": bool_value("balconies"),
            "gear_nook": bool_value("gear_nook"),
            "bike_storage": bool_value("bike_storage"),
            "dog_wash": bool_value("dog_wash"),
            "ev_ready": bool_value("ev_ready"),
        },
    }


def build_context_payload(guardrails: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "label": guardrails.get("label"),
        "allowed_product_types": guardrails.get("allowed_product_types", []),
        "min_year_built": guardrails.get("min_year_built"),
        "min_unit_size": guardrails.get("min_unit_size", {}),
        "min_ceiling_ft": guardrails.get("min_ceiling_ft"),
        "require_wd_in_unit": guardrails.get("require_wd_in_unit", False),
        "parking_ratio_required": guardrails.get("parking_ratio_required"),
    }


def convert_flags(raw_flags: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    converted: List[Dict[str, Any]] = []
    for flag in raw_flags:
        data = flag.get("data") if isinstance(flag.get("data"), Mapping) else {}
        converted.append(
            {
                "code": flag.get("code", "UNKNOWN"),
                "severity": flag.get("severity", "info"),
                "message": flag.get("message", ""),
                "observed": data.get("observed") or data.get("size") or data.get("current"),
                "target": data.get("target") or data.get("min") or data.get("required"),
            }
        )
    return converted


def evaluate_fit(
    *,
    defaults: Mapping[str, Any],
    inputs: Mapping[str, Any],
    guardrails: Mapping[str, Any],
) -> Dict[str, Any]:
    asset_payload = build_asset_payload(defaults, inputs)
    context_payload = build_context_payload(guardrails)
    result = core_fit(asset=asset_payload, context=context_payload)
    return {
        "fit_score": float(result.fit_score),
        "flags": convert_flags(result.flags),
        "context": context_payload,
        "raw_result": result,
    }


REPORT_STORE: Dict[str, Dict[str, Any]] = {}


AUTH_ROLES_SAVE = {"analyst", "admin"}


def save_fit_report(
    *,
    asset_id: str,
    msa_id: Optional[str],
    evaluation: Dict[str, Any],
    context: Mapping[str, Any],
    role: str,
) -> str:
    if role.lower() not in AUTH_ROLES_SAVE:
        raise PermissionError("Insufficient permissions to save fit report")

    report_id = str(uuid.uuid4())
    REPORT_STORE[report_id] = {
        "asset_id": asset_id,
        "msa_id": msa_id,
        "fit_score": evaluation.get("fit_score"),
        "flags": deepcopy(evaluation.get("flags", [])),
        "context": deepcopy(context),
    }
    return report_id
