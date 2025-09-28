"""Calibration helpers translating hazard severity into risk multipliers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class PerilCalibration:
    """Configuration for translating severity indices into multipliers."""

    name: str
    direction: str  # "adverse" or "beneficial"
    slope: float
    deductible_base_bps: float
    deductible_slope_bps: float
    source: str
    description: str


DEFAULT_PERIL_CALIBRATIONS: Dict[str, PerilCalibration] = {
    "wildfire": PerilCalibration(
        name="wildfire",
        direction="adverse",
        slope=0.002,
        deductible_base_bps=150.0,
        deductible_slope_bps=3.0,
        source="USFS WUI Composite",
        description="Wildland-urban interface exposure and suppression resources",
    ),
    "hail": PerilCalibration(
        name="hail",
        direction="adverse",
        slope=0.0022,
        deductible_base_bps=200.0,
        deductible_slope_bps=4.0,
        source="NOAA Storm Events",
        description="Severe convective storm frequency and hail swaths",
    ),
    "snow_load": PerilCalibration(
        name="snow_load",
        direction="adverse",
        slope=0.0018,
        deductible_base_bps=120.0,
        deductible_slope_bps=2.5,
        source="NRCS / ASCE7 Ground Snow Load",
        description="Roof structural demand due to peak ground snow loads",
    ),
    "water_stress": PerilCalibration(
        name="water_stress",
        direction="adverse",
        slope=0.002,
        deductible_base_bps=130.0,
        deductible_slope_bps=3.5,
        source="WRI Aqueduct & US Drought Monitor",
        description="Scarcity of potable water, drought pressure, and tap moratoria",
    ),
    "policy_risk": PerilCalibration(
        name="policy_risk",
        direction="adverse",
        slope=0.0016,
        deductible_base_bps=110.0,
        deductible_slope_bps=2.0,
        source="State & local policy datasets",
        description="Policy friction including rent caps, insurance regulation, and construction moratoria",
    ),
}


def clamp(value: float, *, low: float = 0.90, high: float = 1.10) -> float:
    """Clamp value to the inclusive multiplier bounds."""

    return max(low, min(high, value))


class RiskCalibrator:
    """Translate severity indices into multipliers and deductible guidance."""

    version = "linear_v1"

    def __init__(self, calibrations: Dict[str, PerilCalibration] | None = None) -> None:
        self._calibrations = {
            name.lower(): config for name, config in (calibrations or DEFAULT_PERIL_CALIBRATIONS).items()
        }

    # ------------------------------------------------------------------
    # Core transformations
    # ------------------------------------------------------------------
    def multiplier(self, peril: str, severity_idx: float) -> float:
        """Return the underwriting multiplier for the peril/severity pair."""

        config = self._get_config(peril)
        severity_norm = max(0.0, min(100.0, severity_idx))
        if config.direction == "beneficial":
            base = 0.90
            value = base + severity_norm * config.slope
        else:
            base = 1.10
            value = base - severity_norm * config.slope
        return clamp(value)

    def deductible_guidance(self, peril: str, severity_idx: float) -> dict[str, float | str]:
        """Return deductible guidance expressed in basis points of TIV."""

        config = self._get_config(peril)
        severity_norm = max(0.0, min(100.0, severity_idx))
        recommended = config.deductible_base_bps + severity_norm * config.deductible_slope_bps
        return {
            "recommended_deductible_bps": round(recommended, 2),
            "basis": "total_insured_value",
            "peril": config.name,
            "calibration_note": config.description,
        }

    def source(self, peril: str) -> str:
        """Return the canonical data source label for the peril."""

        return self._get_config(peril).source

    # ------------------------------------------------------------------
    def _get_config(self, peril: str) -> PerilCalibration:
        try:
            return self._calibrations[peril.lower()]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Unsupported peril '{peril}'") from exc


__all__ = ["RiskCalibrator", "PerilCalibration", "DEFAULT_PERIL_CALIBRATIONS"]
