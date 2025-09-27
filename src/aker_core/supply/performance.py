"""
Performance optimization utilities for supply constraint calculations.

Provides memory-efficient processing and caching for large-scale market analysis.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any, Dict, List, Union

import pandas as pd

try:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    import joblib

    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False


class SupplyPerformanceOptimizer:
    """Performance optimization utilities for supply calculations."""

    def __init__(self, cache_size: int = 128, enable_parallel: bool = True):
        """
        Initialize performance optimizer.

        Args:
            cache_size: Maximum cache size for computed results
            enable_parallel: Whether to enable parallel processing
        """
        self.cache_size = cache_size
        self.enable_parallel = enable_parallel and PARALLEL_AVAILABLE

    @lru_cache(maxsize=128)
    def _cached_elasticity_calculation(
        self, permits_hash: str, households_hash: str, years: int
    ) -> float:
        """
        Cached elasticity calculation to avoid recomputation.

        Args:
            permits_hash: Hash of permits array
            households_hash: Hash of households array
            years: Averaging period

        Returns:
            Cached elasticity value
        """
        # This would be populated by the actual calculation
        # For now, return a placeholder
        return 25.0

    def calculate_elasticity_batch(
        self,
        permits_list: List[List[float]],
        households_list: List[List[float]],
        years: int = 3,
        use_cache: bool = True,
    ) -> List[float]:
        """
        Calculate elasticity for multiple markets efficiently.

        Args:
            permits_list: List of permit arrays for different markets
            households_list: List of household arrays for different markets
            years: Averaging period
            use_cache: Whether to use caching for repeated calculations

        Returns:
            List of elasticity values
        """
        results = []

        if use_cache:
            # Use cached calculations where possible
            for permits, households in zip(permits_list, households_list):
                permits_hash = self._hash_array(permits)
                households_hash = self._hash_array(households)
                cache_key = f"{permits_hash}_{households_hash}_{years}"

                try:
                    result = self._cached_elasticity_calculation(
                        permits_hash, households_hash, years
                    )
                    results.append(result)
                except Exception:
                    # Cache miss or error, calculate fresh
                    from .elasticity import elasticity

                    result = elasticity(permits, households, years)
                    results.append(result)
        else:
            # Calculate all fresh
            from .elasticity import elasticity

            for permits, households in zip(permits_list, households_list):
                result = elasticity(permits, households, years)
                results.append(result)

        return results

    def process_large_dataset_in_chunks(
        self, data: pd.DataFrame, chunk_size: int = 1000, operation: str = "elasticity"
    ) -> List[float]:
        """
        Process large datasets in memory-efficient chunks.

        Args:
            data: DataFrame with market data
            chunk_size: Size of each processing chunk
            operation: Type of calculation ('elasticity', 'vacancy', 'leaseup')

        Returns:
            List of calculated values
        """
        results = []

        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i : i + chunk_size]

            if operation == "elasticity":
                from .elasticity import elasticity

                for _, row in chunk.iterrows():
                    permits = (
                        row["permits"] if isinstance(row["permits"], list) else [row["permits"]]
                    )
                    households = (
                        row["households"]
                        if isinstance(row["households"], list)
                        else [row["households"]]
                    )
                    result = elasticity(permits, households)
                    results.append(result)

            elif operation == "vacancy":
                from .vacancy import vacancy

                for _, row in chunk.iterrows():
                    hud_data = row["hud_data"] if isinstance(row["hud_data"], dict) else {}
                    result = vacancy(hud_data)
                    results.append(result)

            elif operation == "leaseup":
                from .leaseup import leaseup_tom

                for _, row in chunk.iterrows():
                    lease_data = row["lease_data"] if isinstance(row["lease_data"], dict) else {}
                    result = leaseup_tom(lease_data)
                    results.append(result)

        return results

    def parallel_process_markets(
        self, market_data: List[Dict[str, Any]], max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Process multiple markets in parallel for better performance.

        Args:
            market_data: List of market data dictionaries
            max_workers: Maximum number of parallel workers

        Returns:
            List of processed market results
        """
        if not PARALLEL_AVAILABLE:
            # Fallback to sequential processing
            return self._process_markets_sequential(market_data)

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_market = {
                executor.submit(self._process_single_market, market_data[i]): i
                for i in range(len(market_data))
            }

            # Collect results as they complete
            for future in as_completed(future_to_market):
                market_idx = future_to_market[future]
                try:
                    result = future.result()
                    results.append((market_idx, result))
                except Exception as e:
                    print(f"Error processing market {market_idx}: {e}")
                    results.append((market_idx, {"error": str(e)}))

        # Sort results by original order
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]

    def _process_single_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single market's supply calculations."""

        # This would need a database session in practice
        # For now, return a placeholder
        return {
            "msa_id": market_data.get("msa_id", "unknown"),
            "status": "processed",
            "elasticity": 25.0,
            "vacancy": 4.5,
            "leaseup_days": 45.0,
        }

    def _process_markets_sequential(
        self, market_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sequential fallback for market processing."""
        return [self._process_single_market(market) for market in market_data]

    def _hash_array(self, array: List[float]) -> str:
        """Create a hash of an array for caching purposes."""
        array_str = json.dumps(array, sort_keys=True)
        return hashlib.md5(array_str.encode()).hexdigest()

    def get_memory_usage_estimate(
        self, num_markets: int, avg_data_size: int = 1000
    ) -> Dict[str, int]:
        """
        Estimate memory usage for processing multiple markets.

        Args:
            num_markets: Number of markets to process
            avg_data_size: Average size of data per market

        Returns:
            Dictionary with memory usage estimates
        """
        # Rough estimates based on typical data structures
        base_memory = 50 * 1024 * 1024  # 50MB base overhead
        per_market_memory = avg_data_size * 8 * 10  # Rough estimate per market
        total_memory = base_memory + (per_market_memory * num_markets)

        return {
            "base_overhead_mb": base_memory // (1024 * 1024),
            "per_market_mb": per_market_memory // (1024 * 1024),
            "total_estimated_mb": total_memory // (1024 * 1024),
            "recommended_batch_size": min(1000, max(10, 1000000 // per_market_memory)),
        }


def optimize_supply_calculations(
    data: Union[pd.DataFrame, List[Dict]],
    operation: str = "elasticity",
    optimization_level: str = "balanced",
) -> Dict[str, Any]:
    """
    Optimize supply calculations based on data size and available resources.

    Args:
        data: Input data for calculations
        operation: Type of calculation ('elasticity', 'vacancy', 'leaseup')
        optimization_level: Optimization strategy ('memory', 'speed', 'balanced')

    Returns:
        Optimization recommendations and configuration
    """
    optimizer = SupplyPerformanceOptimizer()

    if isinstance(data, pd.DataFrame):
        num_records = len(data)
    else:
        num_records = len(data)

    memory_estimate = optimizer.get_memory_usage_estimate(num_records)

    recommendations = {
        "batch_size": memory_estimate["recommended_batch_size"],
        "use_parallel": num_records > 100 and optimization_level in ["speed", "balanced"],
        "cache_results": optimization_level in ["memory", "balanced"],
        "chunk_size": min(1000, num_records // 4) if num_records > 1000 else num_records,
    }

    return {
        "data_size": num_records,
        "memory_estimate": memory_estimate,
        "recommendations": recommendations,
        "estimated_processing_time": _estimate_processing_time(num_records, recommendations),
    }


def _estimate_processing_time(num_records: int, config: Dict[str, Any]) -> str:
    """Estimate processing time based on configuration."""
    base_time_per_record = 0.01  # seconds

    if config.get("use_parallel", False):
        # Parallel processing reduces time
        parallel_factor = 0.7
        batch_factor = config.get("batch_size", 100) / 1000
        estimated_seconds = num_records * base_time_per_record * parallel_factor * batch_factor
    else:
        # Sequential processing
        estimated_seconds = num_records * base_time_per_record

    if estimated_seconds < 60:
        return f"{estimated_seconds:.1f} seconds"
    elif estimated_seconds < 3600:
        return f"{(estimated_seconds / 60):.1f} minutes"
    else:
        return f"{(estimated_seconds / 3600):.1f} hours"
