"""
Risk API endpoints for the GUI application.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/profile")
async def get_risk_profile(
    scope: str = Query(..., regex="^(market|asset)$"),
    msa_id: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
):
    """Get risk profile data for market or asset."""
    if scope == "market" and not msa_id:
        raise HTTPException(status_code=400, detail="msa_id required for market scope")
    if scope == "asset" and not asset_id:
        raise HTTPException(status_code=400, detail="asset_id required for asset scope")

    # This would normally fetch real data from the risk engine
    # For now, return placeholder data
    perils = [
        {
            "peril": "wildfire",
            "severity_idx": 75,
            "insurance_deductible": "$100,000",
            "multiplier": 0.98,
        },
        {
            "peril": "hail",
            "severity_idx": 45,
            "insurance_deductible": "$25,000",
            "multiplier": 0.995,
        },
        {
            "peril": "snow_load",
            "severity_idx": 60,
            "insurance_deductible": "$50,000",
            "multiplier": 0.99,
        },
        {
            "peril": "flood",
            "severity_idx": 30,
            "insurance_deductible": "$100,000",
            "multiplier": 1.0,
        },
        {
            "peril": "water_stress",
            "severity_idx": 80,
            "insurance_deductible": "$75,000",
            "multiplier": 0.97,
        },
    ]

    return {
        "scope": scope,
        "target_id": msa_id or asset_id,
        "perils": perils,
        "last_updated": "2025-01-27T10:00:00Z",
    }


@router.get("/overlays")
async def get_risk_overlays(
    msa_id: str = Query(...),
    perils: Optional[List[str]] = Query(None),
):
    """Get geographic overlay data for risk visualization."""
    if not perils:
        perils = ["wildfire", "hail", "snow_load", "flood", "water_stress"]

    # This would normally return GeoJSON or vector tile data
    # For now, return placeholder structure
    overlays = {}

    for peril in perils:
        overlays[peril] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "severity": 75,
                        "risk_level": "high",
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [-118.0, 34.0],
                            [-117.0, 34.0],
                            [-117.0, 35.0],
                            [-118.0, 35.0],
                            [-118.0, 34.0],
                        ]],
                    },
                }
            ],
        }

    return {
        "msa_id": msa_id,
        "overlays": overlays,
        "last_updated": "2025-01-27T10:00:00Z",
    }


@router.post("/scenario")
async def calculate_insurance_scenario(
    scenario_config: Dict[str, Any],
):
    """Calculate insurance scenario impacts on risk multipliers."""
    # This would normally run complex risk modeling
    # For now, return placeholder calculations

    base_multipliers = {
        "wildfire": 0.98,
        "hail": 0.995,
        "snow_load": 0.99,
        "flood": 1.0,
        "water_stress": 0.97,
    }

    scenario_multipliers = base_multipliers.copy()

    # Apply scenario adjustments (placeholder logic)
    deductibles = scenario_config.get("deductibles", {})
    parametrics = scenario_config.get("parametrics", {})

    # Example adjustments based on deductibles
    for peril, deductible in deductibles.items():
        if deductible == "250000":  # High deductible
            scenario_multipliers[peril] = max(0.9, scenario_multipliers[peril] - 0.02)
        elif deductible == "10000":  # Low deductible
            scenario_multipliers[peril] = min(1.0, scenario_multipliers[peril] + 0.01)

    # Calculate deltas
    multipliers_table = []
    total_exit_cap_delta = 0
    total_contingency_delta = 0

    for peril in base_multipliers:
        base_mult = base_multipliers[peril]
        scenario_mult = scenario_multipliers[peril]
        delta = scenario_mult - base_mult

        multipliers_table.append({
            "peril": peril,
            "base_multiplier": base_mult,
            "scenario_multiplier": scenario_mult,
            "delta": delta,
        })

        # Example impact calculations
        if peril == "wildfire":
            total_exit_cap_delta += delta * 10  # 10 bps impact per 0.01 multiplier change
            total_contingency_delta += abs(delta) * 5  # 5% impact per 0.01 multiplier change

    return {
        "multipliers_table": multipliers_table,
        "exit_cap_bps_delta": total_exit_cap_delta,
        "contingency_pct_delta": total_contingency_delta,
        "scenario_applied": scenario_config,
    }


@router.get("/scenarios")
async def list_risk_scenarios(
    scope: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
):
    """List saved risk scenarios."""
    # This would normally fetch from database
    # For now, return placeholder data
    return {
        "scenarios": [
            {
                "id": "scenario_1",
                "name": "Conservative Coverage",
                "scope": "market",
                "target_id": "14260",
                "created_at": "2025-01-25T10:00:00Z",
            },
            {
                "id": "scenario_2",
                "name": "High Deductible Strategy",
                "scope": "asset",
                "target_id": "AKR-001",
                "created_at": "2025-01-26T14:30:00Z",
            },
        ],
    }
