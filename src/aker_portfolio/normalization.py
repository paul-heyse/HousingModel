from __future__ import annotations

from typing import Optional

from .types import PortfolioPosition


# Simple validation result class
class ValidationResult:
    def __init__(self, is_valid: bool, errors: list[str], warnings: list[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings


class PortfolioPositionNormalizer:
    """Utilities for normalizing and validating portfolio positions."""

    @staticmethod
    def normalize_position_values(positions: list[PortfolioPosition]) -> list[PortfolioPosition]:
        """
        Normalize position values and fill in missing data where possible.

        Args:
            positions: Raw portfolio positions

        Returns:
            Normalized positions with consistent data
        """
        normalized = []

        for pos in positions:
            normalized_pos = PortfolioPositionNormalizer._normalize_single_position(pos)
            if normalized_pos:
                normalized.append(normalized_pos)

        return normalized

    @staticmethod
    def _normalize_single_position(position: PortfolioPosition) -> Optional[PortfolioPosition]:
        """Normalize a single position."""
        # Create a copy to avoid mutating the original
        normalized = PortfolioPosition(
            position_id=position.position_id,
            asset_id=position.asset_id,
            msa_id=position.msa_id,
            strategy=position.strategy,
            state=position.state,
            vintage=position.vintage,
            construction_type=position.construction_type,
            rent_band=position.rent_band,
            position_value=position.position_value,
            units=position.units,
        )

        # Normalize strategy values
        if normalized.strategy:
            normalized.strategy = normalized.strategy.lower().strip()

        # Normalize state values
        if normalized.state:
            normalized.state = normalized.state.upper().strip()

        # Normalize construction type
        if normalized.construction_type:
            normalized.construction_type = normalized.construction_type.lower().strip()

        # Normalize rent band
        if normalized.rent_band:
            normalized.rent_band = normalized.rent_band.lower().strip()

        return normalized

    @staticmethod
    def validate_positions(positions: list[PortfolioPosition]) -> ValidationResult:
        """
        Validate portfolio positions for data quality.

        Args:
            positions: Positions to validate

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        for i, pos in enumerate(positions):
            # Required field validation
            if not pos.position_value or pos.position_value <= 0:
                errors.append(f"Position {i}: Invalid position_value")

            # Data consistency checks
            if pos.asset_id and not pos.msa_id:
                warnings.append(f"Position {i}: Asset specified but no MSA")

            if pos.units and pos.units <= 0:
                errors.append(f"Position {i}: Invalid units count")

            # Geographic consistency
            if pos.msa_id and pos.state:
                # Could add MSA-to-state validation here
                pass

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def infer_missing_data(positions: list[PortfolioPosition]) -> list[PortfolioPosition]:
        """
        Attempt to infer missing data from existing information.

        Args:
            positions: Positions with potentially missing data

        Returns:
            Positions with inferred data where possible
        """
        inferred = []

        for pos in positions:
            inferred_pos = PortfolioPosition(
                position_id=pos.position_id,
                asset_id=pos.asset_id,
                msa_id=pos.msa_id,
                strategy=pos.strategy,
                state=pos.state,
                vintage=pos.vintage,
                construction_type=pos.construction_type,
                rent_band=pos.rent_band,
                position_value=pos.position_value,
                units=pos.units,
            )

            # Infer rent band from position value and units if available
            if not inferred_pos.rent_band and inferred_pos.position_value and inferred_pos.units:
                avg_rent = inferred_pos.position_value / inferred_pos.units
                if avg_rent < 1500:
                    inferred_pos.rent_band = "affordable"
                elif avg_rent < 2500:
                    inferred_pos.rent_band = "workforce"
                elif avg_rent < 4000:
                    inferred_pos.rent_band = "middle"
                else:
                    inferred_pos.rent_band = "luxury"

            # Infer vintage from construction type if missing
            if not inferred_pos.vintage and inferred_pos.construction_type:
                if "new" in inferred_pos.construction_type.lower():
                    inferred_pos.vintage = 2020  # Recent construction
                elif "rehab" in inferred_pos.construction_type.lower():
                    inferred_pos.vintage = 2010  # Recent rehab

            inferred.append(inferred_pos)

        return inferred
