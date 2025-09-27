"""
ETL Pipeline Integration for Supply Constraint Calculators

Provides data extraction, transformation, and loading for supply metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..database.supply import SupplyRepository
from ..supply import calculate_supply_metrics, get_supply_scores_for_scoring
from ..validation.supply_validation import run_supply_validation_cli

logger = logging.getLogger(__name__)


class SupplyETLProcessor:
    """ETL processor for supply constraint metrics."""

    def __init__(self, session):
        """Initialize with database session."""
        self.session = session
        self.repo = SupplyRepository(session)

    def extract_building_permits(self, msa_id: str, years: int = 4) -> List[float]:
        """
        Extract building permit data for an MSA.

        In production, this would connect to permit portals or APIs.
        For now, returns mock data.
        """
        # Mock data - in production this would query permit databases
        mock_permits = {
            "MSA001": [1200, 1350, 1100, 1400],
            "MSA002": [800, 900, 750, 950],
            "MSA003": [1500, 1600, 1450, 1700],
        }

        return mock_permits.get(msa_id, [1000, 1100, 1050, 1150])

    def extract_household_data(self, msa_id: str, years: int = 4) -> List[float]:
        """
        Extract household estimate data for an MSA.

        In production, this would connect to Census Bureau APIs.
        For now, returns mock data.
        """
        # Mock data - in production this would query Census APIs
        mock_households = {
            "MSA001": [52000, 52500, 53000, 53500],
            "MSA002": [35000, 35500, 36000, 36500],
            "MSA003": [75000, 76000, 77000, 78000],
        }

        return mock_households.get(msa_id, [50000, 50500, 51000, 51500])

    def extract_hud_vacancy_data(self, msa_id: str) -> Dict[str, Any]:
        """
        Extract HUD vacancy data for an MSA.

        In production, this would connect to HUD APIs.
        For now, returns mock data.
        """
        # Mock data - in production this would query HUD APIs
        mock_hud_data = {
            "MSA001": {
                "year": [2020, 2021, 2022],
                "vacancy_rate": [5.2, 4.8, 4.5],
                "geography": ["MSA001", "MSA001", "MSA001"],
                "vacancy_type": ["rental", "rental", "rental"],
                "source": ["HUD", "HUD", "HUD"],
            },
            "MSA002": {
                "year": [2020, 2021, 2022],
                "vacancy_rate": [6.1, 5.8, 5.5],
                "geography": ["MSA002", "MSA002", "MSA002"],
                "vacancy_type": ["rental", "rental", "rental"],
                "source": ["HUD", "HUD", "HUD"],
            },
            "MSA003": {
                "year": [2020, 2021, 2022],
                "vacancy_rate": [4.2, 3.9, 3.7],
                "geography": ["MSA003", "MSA003", "MSA003"],
                "vacancy_type": ["rental", "rental", "rental"],
                "source": ["HUD", "HUD", "HUD"],
            },
        }

        return mock_hud_data.get(
            msa_id,
            {
                "year": [2020, 2021, 2022],
                "vacancy_rate": [5.0, 4.7, 4.5],
                "geography": [msa_id, msa_id, msa_id],
                "vacancy_type": ["rental", "rental", "rental"],
                "source": ["HUD", "HUD", "HUD"],
            },
        )

    def extract_lease_data(self, msa_id: str, sample_size: int = 100) -> Dict[str, Any]:
        """
        Extract lease transaction data for an MSA.

        In production, this would connect to property management systems.
        For now, returns mock data.
        """
        # Mock data - in production this would query lease databases
        base_date = datetime(2023, 1, 1)

        mock_lease_data = {
            "MSA001": {
                "lease_date": pd.date_range(base_date, periods=sample_size, freq="D"),
                "property_id": ["PROP001"] * (sample_size // 2) + ["PROP002"] * (sample_size // 2),
                "days_on_market": np.random.randint(10, 60, sample_size).tolist(),
            },
            "MSA002": {
                "lease_date": pd.date_range(base_date, periods=sample_size, freq="D"),
                "property_id": ["PROP003"] * (sample_size // 2) + ["PROP004"] * (sample_size // 2),
                "days_on_market": np.random.randint(15, 75, sample_size).tolist(),
            },
            "MSA003": {
                "lease_date": pd.date_range(base_date, periods=sample_size, freq="D"),
                "property_id": ["PROP005"] * (sample_size // 2) + ["PROP006"] * (sample_size // 2),
                "days_on_market": np.random.randint(8, 45, sample_size).tolist(),
            },
        }

        return mock_lease_data.get(
            msa_id,
            {
                "lease_date": pd.date_range(base_date, periods=sample_size, freq="D"),
                "property_id": ["PROP_DEFAULT"] * sample_size,
                "days_on_market": np.random.randint(10, 60, sample_size).tolist(),
            },
        )

    def process_msa_supply_data(self, msa_id: str, data_vintage: str) -> Dict[str, Any]:
        """
        Process supply data for a single MSA.

        Args:
            msa_id: MSA identifier
            data_vintage: Data vintage string

        Returns:
            Processing results
        """
        try:
            logger.info(f"Processing supply data for MSA {msa_id}")

            # Extract data from various sources
            permits = self.extract_building_permits(msa_id)
            households = self.extract_household_data(msa_id)
            hud_data = self.extract_hud_vacancy_data(msa_id)
            lease_data = self.extract_lease_data(msa_id)

            # Calculate and persist metrics
            result = calculate_supply_metrics(
                session=self.session,
                msa_id=msa_id,
                permits_data=permits,
                households_data=households,
                hud_vacancy_data=hud_data,
                lease_data=lease_data,
                data_vintage=data_vintage,
            )

            logger.info(f"Successfully processed supply data for MSA {msa_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process supply data for MSA {msa_id}: {e}")
            raise

    def process_multiple_msas(self, msa_ids: List[str], data_vintage: str) -> Dict[str, Any]:
        """
        Process supply data for multiple MSAs.

        Args:
            msa_ids: List of MSA identifiers
            data_vintage: Data vintage string

        Returns:
            Processing results for all MSAs
        """
        from ..supply.performance import SupplyPerformanceOptimizer

        optimizer = SupplyPerformanceOptimizer()
        results = {}

        # Optimize processing strategy based on data size
        optimization_config = optimizer.optimize_supply_calculations(
            data=[{"msa_id": msa_id} for msa_id in msa_ids], operation="multiple_msas"
        )

        logger.info(
            f"Processing {len(msa_ids)} MSAs with optimization: {optimization_config['recommendations']}"
        )

        # Process MSAs (in production, this could use parallel processing)
        for msa_id in msa_ids:
            try:
                result = self.process_msa_supply_data(msa_id, data_vintage)
                results[msa_id] = {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to process MSA {msa_id}: {e}")
                results[msa_id] = {"status": "error", "error": str(e)}

        return {
            "processed_msas": len([r for r in results.values() if r["status"] == "success"]),
            "failed_msas": len([r for r in results.values() if r["status"] == "error"]),
            "results": results,
            "optimization_used": optimization_config,
        }

    def validate_supply_pipeline(self, msa_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate the entire supply calculation pipeline.

        Args:
            msa_ids: Optional list of MSA IDs to validate

        Returns:
            Validation results
        """
        try:
            # Run Great Expectations validation
            validation_results = run_supply_validation_cli(self.session, msa_ids)

            # Check data quality
            quality_check = validate_supply_data_quality(self.session, msa_ids)

            return {
                "validation_success": validation_results.get("validation_success", False),
                "data_quality": quality_check["overall_quality"],
                "quality_checks": quality_check["quality_checks"],
                "validation_details": validation_results,
            }

        except Exception as e:
            logger.error(f"Pipeline validation failed: {e}")
            return {"error": str(e), "validation_success": False}

    def get_supply_metrics_for_scoring(self, msa_id: str) -> Dict[str, float]:
        """
        Get supply metrics formatted for pillar scoring.

        Args:
            msa_id: MSA identifier

        Returns:
            Supply constraint scores for scoring pipeline
        """
        try:
            return get_supply_scores_for_scoring(self.session, msa_id)
        except Exception as e:
            logger.error(f"Failed to get supply scores for MSA {msa_id}: {e}")
            raise


def run_supply_etl_pipeline(
    session, msa_ids: List[str], data_vintage: str, validate_results: bool = True
) -> Dict[str, Any]:
    """
    Run the complete supply ETL pipeline.

    Args:
        session: Database session
        msa_ids: List of MSA IDs to process
        data_vintage: Data vintage string
        validate_results: Whether to run validation after processing

    Returns:
        Complete pipeline results
    """
    processor = SupplyETLProcessor(session)

    # Process supply data
    processing_results = processor.process_multiple_msas(msa_ids, data_vintage)

    # Validate results if requested
    validation_results = None
    if validate_results:
        validation_results = processor.validate_supply_pipeline(msa_ids)

    return {
        "processing": processing_results,
        "validation": validation_results,
        "data_vintage": data_vintage,
        "processed_at": datetime.now().isoformat(),
    }


def create_supply_data_pipeline_config() -> Dict[str, Any]:
    """
    Create configuration for supply data pipeline.

    Returns:
        Pipeline configuration dictionary
    """
    return {
        "data_sources": {
            "building_permits": {
                "type": "api",
                "endpoints": ["local_permit_portals", "census_bureau"],
                "refresh_frequency": "monthly",
            },
            "household_estimates": {
                "type": "api",
                "endpoints": ["census_acs_api"],
                "refresh_frequency": "annual",
            },
            "hud_vacancy": {
                "type": "api",
                "endpoints": ["hud_api"],
                "refresh_frequency": "quarterly",
            },
            "lease_transactions": {
                "type": "database",
                "endpoints": ["property_management_systems"],
                "refresh_frequency": "weekly",
            },
        },
        "processing": {
            "batch_size": 100,
            "parallel_processing": True,
            "max_workers": 4,
            "retry_attempts": 3,
        },
        "validation": {
            "enable_great_expectations": True,
            "validation_frequency": "post_processing",
            "quality_thresholds": {"min_data_completeness": 0.8, "max_outlier_percentage": 0.1},
        },
        "monitoring": {
            "enable_logging": True,
            "log_level": "INFO",
            "enable_metrics": True,
            "alert_thresholds": {"processing_failure_rate": 0.05, "data_quality_score": 0.9},
        },
    }
