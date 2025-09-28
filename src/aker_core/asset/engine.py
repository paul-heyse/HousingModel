from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass
class AssetFitResult:
    fit_score: float
    flags: List[Dict[str, Any]] = field(default_factory=list)
    context_label: Optional[str] = None
    ruleset_version: str = "v1"
    inputs: Optional[Dict[str, Any]] = None

    def to_scenario_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for f in self.flags:
            rows.append(
                {
                    "code": f.get("code"),
                    "message": f.get("message"),
                    "severity": f.get("severity"),
                    "context_label": self.context_label,
                    "ruleset_version": self.ruleset_version,
                }
            )
        if not rows:
            rows.append(
                {
                    "code": "OK",
                    "message": "All checks passed",
                    "severity": "info",
                    "context_label": self.context_label,
                    "ruleset_version": self.ruleset_version,
                }
            )
        return rows


def _add_flag(flags: List[Dict[str, Any]], code: str, message: str, severity: str = "info", data: Optional[Mapping[str, Any]] = None) -> None:
    payload = {"code": code, "message": message, "severity": severity}
    if data:
        payload["data"] = dict(data)
    flags.append(payload)


def _bounded(x: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, x))


def fit(*, asset: Mapping[str, Any], context: Mapping[str, Any]) -> AssetFitResult:
    """Evaluate asset fit against guardrails and return score and flags.

    Expected asset fields: product_type, year_built, unit_mix (list of {type, pct, size_sqft}),
    ceiling_min_ft, wd_in_unit (bool), parking_ratio.

    Expected context fields: msa_id, label (e.g., transit-rich), policy thresholds.
    """
    flags: List[Dict[str, Any]] = []
    score = 100.0

    product_type = asset.get("product_type")
    allowed_types: Iterable[str] = context.get("allowed_product_types", [])
    if allowed_types and product_type not in allowed_types:
        _add_flag(flags, "PRODUCT_TYPE_DISALLOWED", f"Product type {product_type} not allowed in context", "error")
        score -= 25

    year_built = asset.get("year_built")
    min_year = context.get("min_year_built")
    if isinstance(year_built, int) and isinstance(min_year, int) and year_built < min_year:
        _add_flag(flags, "VINTAGE_BELOW_MIN", f"Year built {year_built} below min {min_year}", "warn")
        score -= 10

    unit_mix = asset.get("unit_mix") or []
    min_size_by_type: Mapping[str, float] = context.get("min_unit_size", {})
    for u in unit_mix:
        utype = u.get("type")
        size = u.get("size_sqft")
        min_size = min_size_by_type.get(utype)
        if isinstance(min_size, (int, float)) and isinstance(size, (int, float)) and size < float(min_size):
            _add_flag(flags, "UNIT_SIZE_UNDERSPEC", f"{utype} size {size} < {min_size}", "warn", {"unit_type": utype, "size": size, "min": min_size})
            score -= 5

    ceiling_min_ft = asset.get("ceiling_min_ft")
    min_ceiling = context.get("min_ceiling_ft")
    if isinstance(ceiling_min_ft, (int, float)) and isinstance(min_ceiling, (int, float)) and ceiling_min_ft < float(min_ceiling):
        _add_flag(flags, "CEILING_BELOW_MIN", f"Ceiling {ceiling_min_ft} < {min_ceiling}", "warn")
        score -= 5

    wd_in_unit = bool(asset.get("wd_in_unit"))
    require_wd = bool(context.get("require_wd_in_unit", False))
    if require_wd and not wd_in_unit:
        _add_flag(flags, "WASHER_DRYER_REQUIRED", "In-unit W/D required by policy", "error")
        score -= 15

    parking_ratio = asset.get("parking_ratio")
    required_parking = context.get("parking_ratio_required")
    if isinstance(parking_ratio, (int, float)) and isinstance(required_parking, (int, float)):
        if parking_ratio < float(required_parking):
            _add_flag(flags, "PARKING_SHORTFALL", f"Parking {parking_ratio} < {required_parking}", "warn")
            score -= 10

    return AssetFitResult(
        fit_score=_bounded(score),
        flags=flags,
        context_label=context.get("label"),
        ruleset_version="v1",
        inputs={"asset": dict(asset), "context": dict(context)},
    )
