from __future__ import annotations

from sqlalchemy.orm import Session

from .types import ExposureDimension


class GeographicExposureAnalyzer:
    """Geographic-specific exposure analysis utilities."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        # Note: TerrainDataSource integration can be added later when available

    def analyze_geographic_concentrations(
        self, exposures: list[ExposureDimension]
    ) -> dict[str, dict]:
        """
        Analyze geographic concentrations for risk assessment.

        Returns:
            Dictionary with concentration metrics by geography type
        """
        msa_exposures = [exp for exp in exposures if exp.dimension_type == "msa"]
        state_exposures = [exp for exp in exposures if exp.dimension_type == "state"]

        analysis = {
            "msa": self._analyze_msa_concentrations(msa_exposures),
            "state": self._analyze_state_concentrations(state_exposures),
        }

        return analysis

    def _analyze_msa_concentrations(self, msa_exposures: list[ExposureDimension]) -> dict:
        """Analyze MSA-level concentration patterns."""
        if not msa_exposures:
            return {}

        # Sort by exposure percentage
        sorted_exposures = sorted(msa_exposures, key=lambda x: x.exposure_pct, reverse=True)

        # Calculate concentration metrics
        top_3_pct = sum(exp.exposure_pct for exp in sorted_exposures[:3])
        top_1_pct = sorted_exposures[0].exposure_pct if sorted_exposures else 0

        return {
            "top_1_exposure_pct": top_1_pct,
            "top_3_exposure_pct": top_3_pct,
            "concentration_ratio": top_1_pct / sum(exp.exposure_pct for exp in sorted_exposures) if sorted_exposures else 0,
            "num_msas": len(msa_exposures),
            "msa_details": [
                {
                    "msa_id": exp.dimension_value,
                    "exposure_pct": exp.exposure_pct,
                    "exposure_value": exp.exposure_value,
                }
                for exp in sorted_exposures[:10]  # Top 10
            ],
        }

    def _analyze_state_concentrations(self, state_exposures: list[ExposureDimension]) -> dict:
        """Analyze state-level concentration patterns."""
        if not state_exposures:
            return {}

        # Sort by exposure percentage
        sorted_exposures = sorted(state_exposures, key=lambda x: x.exposure_pct, reverse=True)

        # Calculate concentration metrics
        top_3_pct = sum(exp.exposure_pct for exp in sorted_exposures[:3])
        top_1_pct = sorted_exposures[0].exposure_pct if sorted_exposures else 0

        return {
            "top_1_exposure_pct": top_1_pct,
            "top_3_exposure_pct": top_3_pct,
            "concentration_ratio": top_1_pct / sum(exp.exposure_pct for exp in sorted_exposures) if sorted_exposures else 0,
            "num_states": len(state_exposures),
            "state_details": [
                {
                    "state": exp.dimension_value,
                    "exposure_pct": exp.exposure_pct,
                    "exposure_value": exp.exposure_value,
                }
                for exp in sorted_exposures[:10]  # Top 10
            ],
        }

    def get_geographic_risk_factors(self, msa_id: str) -> dict:
        """Get geographic risk factors for a specific MSA."""
        # This would integrate with existing geographic data
        # For now, return placeholder structure
        return {
            "msa_id": msa_id,
            "natural_hazards": {
                "flood_risk": "medium",
                "wildfire_risk": "low",
                "earthquake_risk": "low",
            },
            "regulatory_risk": {
                "rent_control": False,
                "inclusionary_zoning": True,
                "environmental_restrictions": "moderate",
            },
            "market_risk": {
                "supply_elasticity": "moderate",
                "demand_volatility": "low",
                "competition_level": "high",
            },
        }
