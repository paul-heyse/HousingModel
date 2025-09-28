"""Asset API endpoints backing the Asset Fit Wizard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, validator

from ..data.assets import (
    get_asset,
    get_default_form_inputs,
    get_guardrails,
    get_product_default,
    list_assets,
)
from ..services.asset_fit import REPORT_STORE, evaluate_fit, save_fit_report

router = APIRouter()


class UnitMixItem(BaseModel):
    type: str
    pct: Optional[float] = None
    size_sqft: Optional[float] = Field(None, alias="size")


class AssetFitInputs(BaseModel):
    product_type: Optional[str] = None
    year_built: Optional[int] = None
    total_units: Optional[int] = None
    unit_mix: Optional[List[UnitMixItem]] = None
    ceiling_min_ft: Optional[float] = None
    wd_in_unit: Optional[bool] = None
    balconies: Optional[bool] = None
    gear_nook: Optional[bool] = None
    bike_storage: Optional[bool] = None
    dog_wash: Optional[bool] = None
    ev_ready: Optional[bool] = None
    parking_ratio_observed: Optional[float] = None
    parking_context: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "allow"


class AssetFitRequest(BaseModel):
    asset_id: str
    inputs: AssetFitInputs
    persist: bool = False


class AssetFitFlag(BaseModel):
    code: str
    severity: str
    message: str
    observed: Optional[Any] = None
    target: Optional[Any] = None


class AssetFitResponse(BaseModel):
    asset_id: str
    msa_id: Optional[str]
    fit_score: float
    flags: List[AssetFitFlag]
    persisted: bool = False
    fit_report_id: Optional[str] = None


class GuardrailsResponse(BaseModel):
    msa_id: str
    label: str
    allowed_product_types: List[str]
    min_year_built: Optional[int]
    min_unit_size: Dict[str, float]
    min_ceiling_ft: Optional[float]
    require_wd_in_unit: bool
    parking_ratio_required: Optional[float]
    product_defaults: Dict[str, Dict[str, Any]]


@router.get("/")
async def list_assets_endpoint() -> Dict[str, Any]:
    """List available fixture assets."""

    return {"assets": list_assets()}


@router.get("/{asset_id}")
async def get_asset_endpoint(asset_id: str) -> Dict[str, Any]:
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/defaults")
async def get_asset_defaults_endpoint(asset_id: str) -> Dict[str, Any]:
    defaults = get_default_form_inputs(asset_id)
    if not defaults:
        raise HTTPException(status_code=404, detail="Asset defaults not found")
    return defaults


@router.get("/guardrails")
async def get_guardrails_endpoint(msa_id: str) -> GuardrailsResponse:
    guardrails = get_guardrails(msa_id)
    if not guardrails:
        raise HTTPException(status_code=404, detail="Guardrails unavailable for MSA")
    return GuardrailsResponse(
        msa_id=msa_id.upper(),
        label=guardrails.get("label", ""),
        allowed_product_types=guardrails.get("allowed_product_types", []),
        min_year_built=guardrails.get("min_year_built"),
        min_unit_size=guardrails.get("min_unit_size", {}),
        min_ceiling_ft=guardrails.get("min_ceiling_ft"),
        require_wd_in_unit=guardrails.get("require_wd_in_unit", False),
        parking_ratio_required=guardrails.get("parking_ratio_required"),
        product_defaults=guardrails.get("product_defaults", {}),
    )


@router.post("/fit", response_model=AssetFitResponse)
async def calculate_asset_fit(
    payload: AssetFitRequest,
    request: Request,
    x_user_role: str = Header("analyst", alias="X-User-Role"),
) -> AssetFitResponse:
    asset_defaults = get_default_form_inputs(payload.asset_id)
    if not asset_defaults:
        raise HTTPException(status_code=404, detail="Asset not found")

    msa_id = asset_defaults.get("msa_id")
    guardrails = get_guardrails(msa_id)
    if not guardrails:
        raise HTTPException(status_code=503, detail="Guardrails unavailable; Fit Score disabled")

    evaluation = evaluate_fit(
        defaults=asset_defaults,
        inputs=payload.inputs.model_dump(by_alias=True),
        guardrails=guardrails,
    )
    fit_score = evaluation["fit_score"]
    converted_flags = [AssetFitFlag(**flag) for flag in evaluation["flags"]]

    result = evaluation["raw_result"]
    context_payload = evaluation["context"]

    persisted = False
    fit_report_id: Optional[str] = None
    if payload.persist:
        try:
            fit_report_id = save_fit_report(
                asset_id=payload.asset_id,
                msa_id=msa_id,
                evaluation=evaluation,
                context=context_payload,
                role=x_user_role,
            )
            persisted = True
        except PermissionError:
            raise HTTPException(status_code=403, detail="Insufficient permissions to save fit report") from None

    return AssetFitResponse(
        asset_id=payload.asset_id,
        msa_id=msa_id,
        fit_score=fit_score,
        flags=converted_flags,
        persisted=persisted,
        fit_report_id=fit_report_id,
    )


@router.get("/{asset_id}/defaults/{product_type}")
async def get_product_defaults(asset_id: str, product_type: str) -> Dict[str, Any]:
    defaults = get_product_default(asset_id, product_type)
    if not defaults:
        raise HTTPException(status_code=404, detail="Product defaults not available")
    return defaults
