"""Performance benchmarks for ops module."""

import time

import pytest

from aker_core.ops import optimize_cadence


class TestOpsPerformance:
    """Performance tests for operations module."""

    def test_optimize_cadence_performance_small(self):
        """Benchmark small-scale optimization."""
        start_time = time.time()
        plan = optimize_cadence(units=100, downtime_wk=2, vacancy_cap=0.1)
        end_time = time.time()

        assert plan.total_units == 100
        assert end_time - start_time < 0.01  # Should complete in < 10ms

    def test_optimize_cadence_performance_medium(self):
        """Benchmark medium-scale optimization."""
        start_time = time.time()
        plan = optimize_cadence(units=1000, downtime_wk=3, vacancy_cap=0.05)
        end_time = time.time()

        assert plan.total_units == 1000
        assert end_time - start_time < 0.05  # Should complete in < 50ms

    def test_optimize_cadence_performance_large(self):
        """Benchmark large-scale optimization."""
        start_time = time.time()
        plan = optimize_cadence(units=5000, downtime_wk=2, vacancy_cap=0.02)
        end_time = time.time()

        assert plan.total_units == 5000
        assert end_time - start_time < 0.1  # Should complete in < 100ms

    def test_optimize_cadence_memory_efficiency(self):
        """Test that memory usage remains reasonable."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run optimization for large dataset
        plan = optimize_cadence(units=2000, downtime_wk=3, vacancy_cap=0.03)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert plan.total_units == 2000
        assert memory_increase < 10  # Memory increase should be < 10MB

    @pytest.mark.performance
    def test_optimize_cadence_scaling_analysis(self):
        """Analyze performance scaling with different input sizes."""
        sizes = [50, 100, 500, 1000, 2000]
        times = []

        for size in sizes:
            start_time = time.time()
            optimize_cadence(units=size, downtime_wk=2, vacancy_cap=0.1)
            end_time = time.time()
            times.append(end_time - start_time)

        # Verify roughly linear scaling
        # Each doubling of size should roughly double execution time
        assert times[1] / times[0] < 3.0  # 100 vs 50 units
        assert times[3] / times[2] < 3.0  # 1000 vs 500 units

        # Verify reasonable absolute performance
        assert all(t < 0.1 for t in times)  # All should be < 100ms
