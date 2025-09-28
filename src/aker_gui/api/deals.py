"""Deal API endpoints supporting the Deal Workspace UI."""

from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory data stores (demo only – replace with real services in production)
# ---------------------------------------------------------------------------

ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "AKR-123": {
        "asset_id": "AKR-123",
        "msa_id": "BOI",
        "name": "Ridgeline Commons",
        "units": 120,
        "year_built": 2014,
        "product_type": "Garden",
        "parking_context": "Surface (1.2 / unit)",
        "current_rent": 1485,
        "occupancy": 0.94,
        "market_score": 4.1,
        "risk_multiplier": 1.05,
        "msa_name": "Boise, ID",
        "is_admin": True,
    },
    "AKR-987": {
        "asset_id": "AKR-987",
        "msa_id": "DEN",
        "name": "Colfax Lofts",
        "units": 82,
        "year_built": 2001,
        "product_type": "Midrise",
        "parking_context": "Structured (0.9 / unit)",
        "current_rent": 1895,
        "occupancy": 0.92,
        "market_score": 4.4,
        "risk_multiplier": 1.08,
        "msa_name": "Denver, CO",
        "is_admin": False,
    },
}

SCOPE_CATALOG: List[Dict[str, Any]] = [
    {
        "scope_id": "light_interior",
        "name": "Light Unit Refresh",
        "category": "light",
        "cost_per_door": 6500,
        "expected_lift": 85,
        "payback_mo": 24,
        "downtime_wk": 1,
        "retention_bps": 15,
        "default_on": True,
    },
    {
        "scope_id": "medium_reno",
        "name": "Medium Interior Renovation",
        "category": "medium",
        "cost_per_door": 12500,
        "expected_lift": 155,
        "payback_mo": 32,
        "downtime_wk": 2,
        "retention_bps": 25,
        "default_on": False,
    },
    {
        "scope_id": "amenity_refresh",
        "name": "Amenity Upgrade Package",
        "category": "amenity",
        "cost_per_door": 4300,
        "expected_lift": 40,
        "payback_mo": 28,
        "downtime_wk": 0,
        "retention_bps": 45,
        "default_on": False,
    },
    {
        "scope_id": "tech_stack",
        "name": "Smart Home Tech Stack",
        "category": "tech",
        "cost_per_door": 2100,
        "expected_lift": 22,
        "payback_mo": 18,
        "downtime_wk": 0,
        "retention_bps": 30,
        "default_on": True,
    },
    {
        "scope_id": "heavy_reposition",
        "name": "Heavy Reposition",
        "category": "heavy",
        "cost_per_door": 24500,
        "expected_lift": 310,
        "payback_mo": 40,
        "downtime_wk": 4,
        "retention_bps": 55,
        "default_on": False,
    },
]

_SCOPE_CACHE: Dict[str, Any] = {"expires": datetime.min, "data": None}

SCENARIO_STORE: Dict[str, deque] = {}

MANDATE_PAYBACK_THRESHOLD = 36  # months
VACANCY_CAP = 0.08

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ScopeOverride(BaseModel):
    cost_per_door: Optional[float] = Field(None, ge=0)
    expected_lift: Optional[float] = Field(None, ge=0)
    downtime_wk: Optional[float] = Field(None, ge=0)


class RankRequest(BaseModel):
    asset_id: str
    selected_scopes: List[str]
    overrides: Dict[str, ScopeOverride] = Field(default_factory=dict)

    @validator("selected_scopes")
    def validate_scopes(cls, value: List[str]) -> List[str]:
        if len(value) > len(SCOPE_CATALOG):
            raise ValueError("Too many scopes selected")
        return value


class LadderEntry(BaseModel):
    scope_id: str
    scope_name: str
    roi_rank: int
    npv: float
    irr: float
    payback_mo: float
    cost: float
    lift: float
    retention_bps: float
    notes: Optional[str]


class DowntimePoint(BaseModel):
    week: int
    units_offline: int
    vacancy_cap: float


class RankResponse(BaseModel):
    ladder: List[LadderEntry]
    downtime_schedule: List[DowntimePoint]
    totals: Dict[str, float]
    warnings: List[str]
    compute_time_ms: int


class ScenarioPayload(BaseModel):
    asset_id: str
    scenario_name: Optional[str]
    selected_scopes: List[str]
    overrides: Dict[str, ScopeOverride]
    scenario_id: Optional[str] = None


class ScenarioResponse(BaseModel):
    scenario_id: str
    saved_at: datetime


class ScenarioSummary(BaseModel):
    scenario_id: str
    scenario_name: str
    saved_at: datetime


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_asset(asset_id: str) -> Dict[str, Any]:
    asset = ASSET_REGISTRY.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _get_scope_catalog() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    if _SCOPE_CACHE["data"] and _SCOPE_CACHE["expires"] > now:
        return _SCOPE_CACHE["data"]

    catalog = [scope.copy() for scope in SCOPE_CATALOG]
    _SCOPE_CACHE["data"] = catalog
    _SCOPE_CACHE["expires"] = now + timedelta(minutes=10)
    return catalog


def _catalog_by_id() -> Dict[str, Dict[str, Any]]:
    return {scope["scope_id"]: scope for scope in _get_scope_catalog()}


def _calculate_rank(request: RankRequest) -> RankResponse:
    asset = _get_asset(request.asset_id)
    catalog = _catalog_by_id()
    units = asset.get("units", 1)

    ladder: List[LadderEntry] = []
    warnings: List[str] = []

    for scope_id in request.selected_scopes:
        if scope_id not in catalog:
            raise HTTPException(status_code=400, detail=f"Unknown scope_id '{scope_id}'")
        scope = catalog[scope_id]
        override = request.overrides.get(scope_id, ScopeOverride())

        cost_per_door = override.cost_per_door if override.cost_per_door is not None else scope["cost_per_door"]
        lift_per_unit = override.expected_lift if override.expected_lift is not None else scope["expected_lift"]
        downtime_wk = override.downtime_wk if override.downtime_wk is not None else scope["downtime_wk"]

        total_cost = cost_per_door * units
        monthly_lift = lift_per_unit * units
        annual_lift = monthly_lift * 12
        payback = total_cost / monthly_lift if monthly_lift else float("inf")
        irr = min((annual_lift / total_cost) * 100 if total_cost else 0, 35)
        npv = annual_lift * 5 - total_cost

        note = None
        if payback > MANDATE_PAYBACK_THRESHOLD:
            warnings.append(
                f"Scope {scope['name']} exceeds mandate threshold ({payback:.1f} months)"
            )
            note = "Payback exceeds mandate threshold (36 months)"

        ladder.append(
            LadderEntry(
                scope_id=scope_id,
                scope_name=scope["name"],
                roi_rank=0,  # placeholder, sorted later
                npv=npv,
                irr=irr,
                payback_mo=payback,
                cost=total_cost,
                lift=monthly_lift,
                retention_bps=scope.get("retention_bps", 0),
                notes=note,
            )
        )

    ladder.sort(key=lambda entry: entry.npv, reverse=True)
    for idx, entry in enumerate(ladder, start=1):
        entry.roi_rank = idx

    downtime_schedule = _build_downtime_schedule(ladder, units)
    totals = _compute_totals(ladder)

    return RankResponse(
        ladder=ladder,
        downtime_schedule=downtime_schedule,
        totals=totals,
        warnings=warnings,
        compute_time_ms=0,
    )


def _build_downtime_schedule(ladder: List[LadderEntry], units: int) -> List[DowntimePoint]:
    if not ladder:
        return []

    timeline: List[DowntimePoint] = []
    week = 1
    for entry in ladder:
        downtime_weeks = max(int(round(entry.payback_mo / 6)), 1)
        per_week = int(max(units * 0.05, 1))
        for i in range(downtime_weeks):
            timeline.append(
                DowntimePoint(
                    week=week,
                    units_offline=min(units, per_week * (i + 1)),
                    vacancy_cap=VACANCY_CAP * units,
                )
            )
            week += 1
    return timeline


def _compute_totals(ladder: List[LadderEntry]) -> Dict[str, float]:
    total_cost = sum(entry.cost for entry in ladder)
    total_lift = sum(entry.lift for entry in ladder)
    total_retention = sum(entry.retention_bps for entry in ladder)
    average_payback = sum(entry.payback_mo for entry in ladder) / len(ladder) if ladder else 0

    return {
        "total_cost": total_cost,
        "total_lift": total_lift,
        "total_retention_bps": total_retention,
        "avg_payback_mo": average_payback,
    }


def _save_scenario(payload: ScenarioPayload) -> ScenarioResponse:
    scenario_id = payload.scenario_id or str(uuid4())
    saved_at = datetime.utcnow()

    entry = {
        "scenario_id": scenario_id,
        "scenario_name": payload.scenario_name or f"Scenario {saved_at.strftime('%H:%M:%S')}",
        "saved_at": saved_at,
        "selected_scopes": payload.selected_scopes,
        "overrides": payload.overrides,
    }

    queue = SCENARIO_STORE.setdefault(payload.asset_id, deque(maxlen=5))

    # If scenario exists, replace it; otherwise append
    for index, existing in enumerate(queue):
        if existing["scenario_id"] == scenario_id:
            queue[index] = entry
            break
    else:
        queue.appendleft(entry)

    return ScenarioResponse(scenario_id=scenario_id, saved_at=saved_at)


def _list_scenarios(asset_id: str) -> List[ScenarioSummary]:
    queue = SCENARIO_STORE.get(asset_id, deque())
    return [
        ScenarioSummary(
            scenario_id=item["scenario_id"],
            scenario_name=item["scenario_name"],
            saved_at=item["saved_at"],
        )
        for item in list(queue)
    ]


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------


@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str) -> Dict[str, Any]:
    """Return asset details for the workspace header."""
    return _get_asset(asset_id)


@router.get("/scopes/catalog")
async def get_scope_catalog() -> List[Dict[str, Any]]:
    """Return the scope catalog (cached for 10 minutes)."""
    return _get_scope_catalog()


@router.post("/rank", response_model=RankResponse)
async def rank_scopes(request: RankRequest) -> RankResponse:
    """Rank selected scopes and generate downtime schedule."""
    start = time.time()
    response = _calculate_rank(request)
    response.compute_time_ms = int((time.time() - start) * 1000)
    return response


@router.post("/scenario/save", response_model=ScenarioResponse)
async def save_scenario(payload: ScenarioPayload) -> ScenarioResponse:
    """Persist a scenario for later retrieval."""
    if not payload.selected_scopes:
        raise HTTPException(status_code=400, detail="Cannot save scenario without scopes")
    return _save_scenario(payload)


@router.get("/scenario/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Fetch a persisted scenario object."""
    for queue in SCENARIO_STORE.values():
        for item in queue:
            if item["scenario_id"] == scenario_id:
                return item
    raise HTTPException(status_code=404, detail="Scenario not found")


@router.get("/scenario")
async def list_scenarios(asset_id: str) -> List[ScenarioSummary]:
    """List the most recent scenarios for an asset."""
    return _list_scenarios(asset_id)


# ---------------------------------------------------------------------------
# Convenience helpers for Dash callbacks
# ---------------------------------------------------------------------------


def get_asset_details(asset_id: str) -> Dict[str, Any]:
    """Convenience wrapper used by Dash callbacks."""
    return _get_asset(asset_id)


def get_scope_catalog_cached() -> List[Dict[str, Any]]:
    return _get_scope_catalog()


def rank_deal(payload: RankRequest) -> RankResponse:
    return _calculate_rank(payload)


def list_recent_scenarios(asset_id: str) -> List[ScenarioSummary]:
    return _list_scenarios(asset_id)


def save_deal_scenario(payload: ScenarioPayload) -> ScenarioResponse:
    return _save_scenario(payload)
