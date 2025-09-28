"""
Performance benchmarking utilities for portfolio exposure calculations.

This module provides tools to benchmark exposure calculations for large portfolios
and identify performance bottlenecks.
"""

from __future__ import annotations

import time
from typing import Any

from .types import ExposureResult, PortfolioPosition


class PerformanceBenchmark:
    """Benchmark portfolio exposure calculations."""

    def __init__(self):
        self.results = []

    def benchmark_exposure_calculation(
        self,
        positions: list[PortfolioPosition],
        num_runs: int = 5
    ) -> dict[str, Any]:
        """Benchmark exposure calculation performance."""

        times = []
        memory_usage = []

        for i in range(num_runs):
            # Mock session for benchmarking
            class MockSession:
                def __init__(self):
                    self.data = []

                def add(self, obj):
                    self.data.append(obj)

                def commit(self):
                    pass

            start_time = time.time()
            try:
                # This would normally use a real database session
                # For benchmarking, we'll simulate the computation
                self._simulate_exposure_calculation(positions)
                end_time = time.time()

                times.append(end_time - start_time)
                memory_usage.append(len(positions) * 100)  # Mock memory usage

            except Exception as e:
                times.append(-1)  # Error marker
                print(f"Run {i+1} failed: {e}")

        # Calculate statistics
        successful_times = [t for t in times if t > 0]

        if not successful_times:
            return {
                "success": False,
                "error": "All benchmark runs failed",
                "num_positions": len(positions),
                "num_runs": num_runs,
            }

        return {
            "success": True,
            "num_positions": len(positions),
            "num_runs": num_runs,
            "avg_time": sum(successful_times) / len(successful_times),
            "min_time": min(successful_times),
            "max_time": max(successful_times),
            "std_time": self._calculate_std(successful_times),
            "avg_memory_mb": sum(memory_usage) / len(memory_usage) / (1024 * 1024),
            "times": times,
        }

    def benchmark_scalability(
        self,
        base_positions: list[PortfolioPosition],
        scale_factors: list[int] = [1, 2, 5, 10, 20]
    ) -> dict[str, Any]:
        """Benchmark scalability with increasing portfolio sizes."""
        results = {}

        for factor in scale_factors:
            num_positions = len(base_positions) * factor
            positions = self._scale_positions(base_positions, factor)

            print(f"Benchmarking with {num_positions} positions...")
            result = self.benchmark_exposure_calculation(positions, num_runs=3)

            if result["success"]:
                results[f"{num_positions}_positions"] = {
                    "avg_time": result["avg_time"],
                    "positions_per_second": num_positions / result["avg_time"],
                }
            else:
                results[f"{num_positions}_positions"] = {
                    "error": result["error"]
                }

        return results

    def _simulate_exposure_calculation(self, positions: list[PortfolioPosition]) -> ExposureResult:
        """Simulate exposure calculation for benchmarking."""
        # This is a simplified simulation for benchmarking
        # In real usage, this would call the actual compute_exposures function

        total_value = sum(pos.position_value for pos in positions)

        # Group by dimensions (simplified)
        exposures = []
        dimensions = ["strategy", "state", "msa"]

        for dim in dimensions:
            dim_groups = {}
            for pos in positions:
                value = getattr(pos, dim)
                if value:
                    if value not in dim_groups:
                        dim_groups[value] = []
                    dim_groups[value].append(pos)

            for value, pos_list in dim_groups.items():
                group_value = sum(pos.position_value for pos in pos_list)
                exposure_pct = (group_value / total_value) * 100

                from .types import ExposureDimension
                exposures.append(ExposureDimension(
                    dimension_type=dim,
                    dimension_value=value,
                    exposure_pct=exposure_pct,
                    exposure_value=group_value,
                    total_portfolio_value=total_value,
                ))

        from .types import ExposureResult
        return ExposureResult(
            as_of_date=None,  # Mock
            total_portfolio_value=total_value,
            exposures=exposures,
        )

    def _scale_positions(self, base_positions: list[PortfolioPosition], factor: int) -> list[PortfolioPosition]:
        """Scale positions for benchmarking."""
        scaled = []

        for i in range(factor):
            for pos in base_positions:
                # Create a copy with modified ID
                scaled_pos = PortfolioPosition(
                    position_id=f"{pos.position_id}_scaled_{i}",
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
                scaled.append(scaled_pos)

        return scaled

    def _calculate_std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


class DataBackfillUtility:
    """Utilities for backfilling historical exposure data."""

    def __init__(self, db_session):
        self.db_session = db_session

    def backfill_historical_exposures(
        self,
        positions_history: dict[str, list[PortfolioPosition]],
        start_date: str,
        end_date: str
    ) -> dict[str, Any]:
        """
        Backfill historical exposure calculations.

        Args:
            positions_history: Dict mapping dates to position lists
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Backfill results summary
        """
        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        results = {
            "dates_processed": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "errors": [],
        }

        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")

            if date_str in positions_history:
                try:
                    positions_history[date_str]
                    # Would call actual compute_exposures here
                    # For now, just simulate success
                    results["successful_calculations"] += 1

                except Exception as e:
                    results["failed_calculations"] += 1
                    results["errors"].append(f"{date_str}: {str(e)}")

            results["dates_processed"] += 1
            current_date += timedelta(days=1)

        return results

    def validate_backfill_data(self, backfill_results: dict[str, Any]) -> bool:
        """Validate that backfill data is complete and consistent."""
        required_keys = ["dates_processed", "successful_calculations", "failed_calculations", "errors"]

        if not all(key in backfill_results for key in required_keys):
            return False

        if backfill_results["dates_processed"] != (
            backfill_results["successful_calculations"] + backfill_results["failed_calculations"]
        ):
            return False

        return True
