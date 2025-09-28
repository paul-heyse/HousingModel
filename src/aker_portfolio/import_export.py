"""
Import/export utilities for portfolio positions.

This module provides functionality to import portfolio positions from various
formats and export exposure results to different formats.
"""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any

from .types import ExposureDimension, ExposureResult, PortfolioPosition


class PortfolioPositionImporter:
    """Import portfolio positions from various formats."""

    @staticmethod
    def from_csv(csv_data: str) -> list[PortfolioPosition]:
        """Import positions from CSV format."""
        positions = []
        reader = csv.DictReader(StringIO(csv_data))

        for row in reader:
            position = PortfolioPosition(
                position_id=row.get("position_id"),
                asset_id=row.get("asset_id"),
                msa_id=row.get("msa_id"),
                strategy=row.get("strategy"),
                state=row.get("state"),
                vintage=int(row["vintage"]) if row.get("vintage") and row["vintage"].isdigit() else None,
                construction_type=row.get("construction_type"),
                rent_band=row.get("rent_band"),
                position_value=float(row["position_value"]) if row.get("position_value") else 0.0,
                units=int(row["units"]) if row.get("units") and row["units"].isdigit() else None,
            )
            positions.append(position)

        return positions

    @staticmethod
    def from_json(json_data: str) -> list[PortfolioPosition]:
        """Import positions from JSON format."""
        data = json.loads(json_data)
        positions_data = data if isinstance(data, list) else data.get("positions", [])

        positions = []
        for pos_data in positions_data:
            position = PortfolioPosition(
                position_id=pos_data.get("position_id"),
                asset_id=pos_data.get("asset_id"),
                msa_id=pos_data.get("msa_id"),
                strategy=pos_data.get("strategy"),
                state=pos_data.get("state"),
                vintage=pos_data.get("vintage"),
                construction_type=pos_data.get("construction_type"),
                rent_band=pos_data.get("rent_band"),
                position_value=pos_data.get("position_value", 0.0),
                units=pos_data.get("units"),
            )
            positions.append(position)

        return positions

    @staticmethod
    def from_excel(file_path: str) -> list[PortfolioPosition]:
        """Import positions from Excel file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel import")

        df = pd.read_excel(file_path)

        positions = []
        for _, row in df.iterrows():
            position = PortfolioPosition(
                position_id=str(row.get("position_id")) if pd.notna(row.get("position_id")) else None,
                asset_id=str(row.get("asset_id")) if pd.notna(row.get("asset_id")) else None,
                msa_id=str(row.get("msa_id")) if pd.notna(row.get("msa_id")) else None,
                strategy=str(row.get("strategy")) if pd.notna(row.get("strategy")) else None,
                state=str(row.get("state")) if pd.notna(row.get("state")) else None,
                vintage=int(row["vintage"]) if pd.notna(row.get("vintage")) and str(row["vintage"]).isdigit() else None,
                construction_type=str(row.get("construction_type")) if pd.notna(row.get("construction_type")) else None,
                rent_band=str(row.get("rent_band")) if pd.notna(row.get("rent_band")) else None,
                position_value=float(row["position_value"]) if pd.notna(row.get("position_value")) else 0.0,
                units=int(row["units"]) if pd.notna(row.get("units")) and str(row["units"]).isdigit() else None,
            )
            positions.append(position)

        return positions


class PortfolioExporter:
    """Export portfolio data to various formats."""

    @staticmethod
    def exposures_to_csv(exposures: list[ExposureDimension]) -> str:
        """Export exposures to CSV format."""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "dimension_type", "dimension_value", "exposure_pct",
            "exposure_value", "total_portfolio_value"
        ])

        # Write data
        for exp in exposures:
            writer.writerow([
                exp.dimension_type,
                exp.dimension_value,
                f"{exp.exposure_pct:.2f}",
                f"{exp.exposure_value:,.2f}",
                f"{exp.total_portfolio_value:,.2f}",
            ])

        return output.getvalue()

    @staticmethod
    def exposures_to_json(exposure_result: ExposureResult) -> str:
        """Export exposure result to JSON format."""
        data = {
            "as_of_date": exposure_result.as_of_date.isoformat(),
            "total_portfolio_value": exposure_result.total_portfolio_value,
            "exposures": [
                {
                    "dimension_type": exp.dimension_type,
                    "dimension_value": exp.dimension_value,
                    "exposure_pct": exp.exposure_pct,
                    "exposure_value": exp.exposure_value,
                }
                for exp in exposure_result.exposures
            ]
        }

        return json.dumps(data, indent=2)

    @staticmethod
    def exposures_to_excel(exposures: list[ExposureDimension], file_path: str) -> None:
        """Export exposures to Excel file."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel export")

        # Convert to DataFrame
        df_data = []
        for exp in exposures:
            df_data.append(
                {
                    "Dimension Type": exp.dimension_type,
                    "Dimension Value": exp.dimension_value,
                    "Exposure %": f"{exp.exposure_pct:.2f}%",
                    "Exposure Value": f"${exp.exposure_value:,.2f}",
                    "Portfolio Value": f"${exp.total_portfolio_value:,.2f}",
                }
            )

        df = pd.DataFrame(df_data)

        # Group by dimension type for better organization
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            # Summary sheet
            summary_data = []
            for dim_type in set(exp.dimension_type for exp in exposures):
                dim_exposures = [exp for exp in exposures if exp.dimension_type == dim_type]
                total_pct = sum(exp.exposure_pct for exp in dim_exposures)
                summary_data.append(  # pragma: no branch - simple accumulation
                    {
                        "Dimension": dim_type.title(),
                        "Total Exposure %": f"{total_pct:.2f}%",
                        "Count": len(dim_exposures),
                    }
                )

            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            # Detailed breakdown
            df.to_excel(writer, sheet_name="Detailed Breakdown", index=False)

            # Individual dimension sheets
            for dim_type in set(exp.dimension_type for exp in exposures):
                dim_exposures = [exp for exp in exposures if exp.dimension_type == dim_type]
                dim_df = pd.DataFrame(
                    [
                        {
                            "Value": exp.dimension_value,
                            "Exposure %": f"{exp.exposure_pct:.2f}%",
                            "Exposure Value": f"${exp.exposure_value:,.2f}",
                        }
                        for exp in dim_exposures
                    ]
                )
                dim_df.to_excel(writer, sheet_name=dim_type.title()[:31], index=False)  # Excel sheet name limit


class PortfolioDataValidator:
    """Validate imported portfolio data."""

    @staticmethod
    def validate_positions(positions: list[PortfolioPosition]) -> dict[str, Any]:
        """Validate imported positions and return validation report."""
        errors = []
        warnings = []
        stats = {
            "total_positions": len(positions),
            "total_value": sum(pos.position_value for pos in positions),
            "dimensions_present": set(),
            "missing_data": {},
        }

        for i, pos in enumerate(positions):
            # Check required fields
            if pos.position_value <= 0:
                errors.append(f"Position {i}: Invalid position_value")

            if not pos.position_id:
                warnings.append(f"Position {i}: Missing position_id")

            # Check dimension completeness
            dimensions = ["strategy", "state", "msa_id", "vintage", "construction_type", "rent_band"]
            for dim in dimensions:
                value = getattr(pos, dim)
                if value is not None:
                    stats["dimensions_present"].add(dim)
                else:
                    if dim not in stats["missing_data"]:
                        stats["missing_data"][dim] = 0
                    stats["missing_data"][dim] += 1

            # Check data consistency
            if pos.msa_id and pos.state:
                # Could add MSA-to-state validation
                pass

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": stats,
        }
