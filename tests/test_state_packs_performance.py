"""Performance benchmarks for state rule packs."""

import time

import pytest

from aker_core.state_packs import apply, load_state_rules


class TestStatePacksPerformance:
    """Performance tests for state rule packs."""

    def test_rule_loading_performance(self):
        """Benchmark rule pack loading performance."""
        # Load each state multiple times (should be cached)
        start_time = time.time()

        for _ in range(100):
            co_rules = load_state_rules("CO")
            ut_rules = load_state_rules("UT")
            id_rules = load_state_rules("ID")

        end_time = time.time()

        # Should complete in reasonable time (cached loading)
        assert end_time - start_time < 0.1  # < 100ms for 300 loads

        # Verify rules were loaded correctly
        assert co_rules.state_code == "CO"
        assert ut_rules.state_code == "UT"
        assert id_rules.state_code == "ID"

    def test_rule_application_performance(self):
        """Benchmark rule application performance."""
        context = {
            "insurance_rate": 0.006,
            "entitlement_days": 180,
            "winterization_cost": 5000,
            "hail_risk": 1.0,
            "wildfire_risk": 1.0,
            "water_cost": 1000,
            "migration_factor": 1.0,
            "forest_risk": 1.0
        }

        start_time = time.time()

        # Apply rules to multiple contexts
        for _ in range(1000):
            co_result = apply("CO", context.copy())
            ut_result = apply("UT", context.copy())
            id_result = apply("ID", context.copy())

        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 1.0  # < 1 second for 3000 applications

        # Verify results are correct
        assert co_result["hail_risk_multiplier"] == 1.25
        assert ut_result["water_infrastructure_cost_multiplier"] == 1.22
        assert id_result["migration_demand_multiplier"] == 1.12

    def test_large_context_performance(self):
        """Benchmark performance with large context objects."""
        # Create large context with many fields
        large_context = {f"field_{i}": i * 0.001 for i in range(1000)}

        start_time = time.time()
        result = apply("CO", large_context)
        end_time = time.time()

        # Should handle large contexts efficiently
        assert end_time - start_time < 0.1  # < 100ms
        assert len(result.to_dict()) > 1000  # Should preserve all fields

    def test_memory_usage_efficiency(self):
        """Test that memory usage remains reasonable."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Apply rules many times
        contexts = [
            {"insurance_rate": 0.006, "entitlement_days": 180},
            {"water_cost": 1000, "topography_factor": 1.2},
            {"migration_factor": 1.0, "forest_risk": 0.8}
        ]

        for _ in range(1000):
            for context in contexts:
                apply("CO", context.copy())

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be minimal
        assert memory_increase < 50  # < 50MB increase

    @pytest.mark.performance
    def test_scaling_analysis(self):
        """Analyze performance scaling with context size."""
        sizes = [10, 50, 100, 500, 1000]
        times = []

        for size in sizes:
            # Create context with 'size' fields
            context = {f"field_{i}": i * 0.001 for i in range(size)}

            start_time = time.time()
            result = apply("CO", context)
            end_time = time.time()

            times.append(end_time - start_time)

            # Verify result has expected number of fields
            assert len(result.to_dict()) >= size + 10  # Original + rule additions

        # Verify reasonable scaling (should be roughly linear)
        # Each doubling should roughly double execution time
        for i in range(len(sizes) - 1):
            ratio = times[i + 1] / times[i]
            size_ratio = sizes[i + 1] / sizes[i]
            # Allow some variance due to Python overhead
            assert ratio < size_ratio * 3.0

        # All should complete in reasonable time
        assert all(t < 0.1 for t in times)  # All < 100ms

    def test_cache_effectiveness(self):
        """Test that caching improves performance."""
        context = {"insurance_rate": 0.006, "entitlement_days": 180}

        # First application (cache miss)
        start_time = time.time()
        result1 = apply("CO", context)
        first_time = time.time() - start_time

        # Subsequent applications (cache hit)
        start_time = time.time()
        for _ in range(100):
            result2 = apply("CO", context)
        cached_time = (time.time() - start_time) / 100

        # Cached applications should be significantly faster
        assert cached_time < first_time * 0.5  # At least 50% faster

        # Results should be identical
        assert result1.to_dict() == result2.to_dict()
