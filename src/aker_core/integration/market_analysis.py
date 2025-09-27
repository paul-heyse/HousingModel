"""
Market Analysis Pipeline

Integrates all pillar calculators to produce comprehensive market scores
for the Aker Property Model.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Union
from datetime import date, datetime
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

# Import all pillar calculators
from ..supply import (
    elasticity, vacancy, leaseup_tom,
    inverse_elasticity_score, inverse_vacancy_score, inverse_leaseup_score,
    calculate_supply_metrics, get_supply_scores_for_scoring
)
from ..markets import score, MarketPillarScores

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketAnalysisResult:
    """Complete market analysis results."""

    msa_id: str
    supply_score: float
    jobs_score: float
    urban_score: float
    outdoor_score: float
    final_score_0_5: float
    final_score_0_100: float
    pillar_weights: Dict[str, float]
    analysis_timestamp: datetime
    data_sources: Dict[str, str]
    confidence_score: float


class MarketAnalysisPipeline:
    """Complete market analysis pipeline integrating all pillars."""

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
        self.supply_calculator = SupplyCalculator()
        self.jobs_calculator = JobsCalculator()
        self.urban_calculator = UrbanCalculator()
        self.outdoor_calculator = OutdoorCalculator()

    def analyze_market(
        self,
        msa_id: str,
        as_of: Optional[date] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> MarketAnalysisResult:
        """
        Perform complete market analysis for an MSA.

        Args:
            msa_id: MSA identifier
            as_of: Analysis date
            custom_weights: Custom pillar weights

        Returns:
            Complete market analysis results
        """
        logger.info(f"Starting comprehensive market analysis for {msa_id}")

        try:
            # Get pillar scores from each calculator
            supply_score = self.supply_calculator.get_supply_score(msa_id, as_of)
            jobs_score = self.jobs_calculator.get_jobs_score(msa_id, as_of)
            urban_score = self.urban_calculator.get_urban_score(msa_id, as_of)
            outdoor_score = self.outdoor_calculator.get_outdoor_score(msa_id, as_of)

            # Compose final market score
            final_score = score(
                session=self.session,
                msa_id=msa_id,
                supply_0_5=supply_score / 20,  # Convert 0-100 to 0-5
                jobs_0_5=jobs_score / 20,
                urban_0_5=urban_score / 20,
                outdoor_0_5=outdoor_score / 20,
                weights=custom_weights
            )

            # Calculate confidence score based on data availability
            confidence = self._calculate_confidence_score({
                'supply': supply_score,
                'jobs': jobs_score,
                'urban': urban_score,
                'outdoor': outdoor_score
            })

            return MarketAnalysisResult(
                msa_id=msa_id,
                supply_score=supply_score,
                jobs_score=jobs_score,
                urban_score=urban_score,
                outdoor_score=outdoor_score,
                final_score_0_5=final_score.weighted_0_5,
                final_score_0_100=final_score.weighted_0_100,
                pillar_weights=final_score.weights,
                analysis_timestamp=datetime.now(),
                data_sources=self._get_data_sources(),
                confidence_score=confidence
            )

        except Exception as e:
            logger.error(f"Market analysis failed for {msa_id}: {e}")
            raise

    def _calculate_confidence_score(self, pillar_scores: Dict[str, float]) -> float:
        """Calculate confidence score based on data availability."""
        # Simple confidence calculation based on score completeness
        available_scores = sum(1 for score in pillar_scores.values() if score > 0)
        return min(1.0, available_scores / 4.0)  # 4 pillars

    def _get_data_sources(self) -> Dict[str, str]:
        """Get data source information."""
        return {
            'supply': 'HUD, Census, Local Permits',
            'jobs': 'BLS, BEA, NIH/NSF/DoD',
            'urban': 'OSM, GTFS, Local Retail',
            'outdoor': 'EPA, NOAA, OSM Trails'
        }


class SupplyCalculator:
    """Supply constraint calculator integration."""

    def get_supply_score(self, msa_id: str, as_of: Optional[date] = None) -> float:
        """Get supply constraint score for MSA."""
        try:
            scores = get_supply_scores_for_scoring(self.session, msa_id, as_of)
            return scores['composite_supply_score']
        except Exception:
            logger.warning(f"Supply score not available for {msa_id}")
            return 50.0  # Default neutral score


class JobsCalculator:
    """Innovation jobs calculator integration."""

    def get_jobs_score(self, msa_id: str, as_of: Optional[date] = None) -> float:
        """Get innovation jobs score for MSA."""
        # Placeholder - would integrate with jobs analysis
        logger.warning(f"Jobs calculator not yet implemented for {msa_id}")
        return 50.0  # Default neutral score


class UrbanCalculator:
    """Urban convenience calculator integration."""

    def get_urban_score(self, msa_id: str, as_of: Optional[date] = None) -> float:
        """Get urban convenience score for MSA."""
        # Placeholder - would integrate with urban metrics
        logger.warning(f"Urban calculator not yet implemented for {msa_id}")
        return 50.0  # Default neutral score


class OutdoorCalculator:
    """Outdoor access calculator integration."""

    def get_outdoor_score(self, msa_id: str, as_of: Optional[date] = None) -> float:
        """Get outdoor access score for MSA."""
        # Placeholder - would integrate with outdoor analysis
        logger.warning(f"Outdoor calculator not yet implemented for {msa_id}")
        return 50.0  # Default neutral score


def analyze_market(
    session: Session,
    msa_id: str,
    as_of: Optional[date] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> MarketAnalysisResult:
    """
    Convenience function for market analysis.

    Args:
        session: Database session
        msa_id: MSA identifier
        as_of: Analysis date
        custom_weights: Custom pillar weights

    Returns:
        Complete market analysis results
    """
    pipeline = MarketAnalysisPipeline(session)
    return pipeline.analyze_market(msa_id, as_of, custom_weights)


def analyze_multiple_markets(
    session: Session,
    msa_ids: List[str],
    as_of: Optional[date] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, MarketAnalysisResult]:
    """
    Analyze multiple markets efficiently.

    Args:
        session: Database session
        msa_ids: List of MSA identifiers
        as_of: Analysis date
        custom_weights: Custom pillar weights

    Returns:
        Dictionary mapping MSA IDs to analysis results
    """
    results = {}

    for msa_id in msa_ids:
        try:
            result = analyze_market(session, msa_id, as_of, custom_weights)
            results[msa_id] = result
        except Exception as e:
            logger.error(f"Failed to analyze market {msa_id}: {e}")
            results[msa_id] = None

    return results


def get_market_rankings(
    session: Session,
    msa_ids: List[str],
    as_of: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Get market rankings by final score.

    Args:
        session: Database session
        msa_ids: List of MSA identifiers
        as_of: Analysis date

    Returns:
        List of market rankings sorted by score
    """
    analysis_results = analyze_multiple_markets(session, msa_ids, as_of)

    # Filter out failed analyses and sort by score
    valid_results = [
        {
            'msa_id': msa_id,
            'score_0_5': result.final_score_0_5,
            'score_0_100': result.final_score_0_100,
            'rank': 0  # Will be set below
        }
        for msa_id, result in analysis_results.items()
        if result is not None
    ]

    # Sort by score (descending)
    valid_results.sort(key=lambda x: x['score_0_5'], reverse=True)

    # Assign ranks
    for i, result in enumerate(valid_results):
        result['rank'] = i + 1

    return valid_results
