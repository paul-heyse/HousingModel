"""State pack impact endpoints."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

STATE_PACK_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
    "CO": {"light_interior": 0.07, "medium_reno": 0.09, "amenity_refresh": 0.05},
    "ID": {"light_interior": 0.04, "tech_stack": 0.03},
    "UT": {"heavy_reposition": 0.1},
}


@router.get("/impact")
async def state_pack_impact(state: str, scopes: List[str]) -> Dict[str, float]:
    """Return cost adders for the given state/scopes."""
    state = state.upper()
    if state not in STATE_PACK_ADJUSTMENTS:
        raise HTTPException(status_code=404, detail="State pack not configured")

    adjustments = {
        scope_id: STATE_PACK_ADJUSTMENTS[state].get(scope_id, 0.0)
        for scope_id in scopes
    }
    return adjustments
