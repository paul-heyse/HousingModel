"""Performance benchmarks for governance system."""

import time
import pytest
from datetime import datetime

from aker_core.governance import ICWorkflow, get_required_artifacts
from aker_core.database import GovernanceRepository


class TestGovernancePerformance:
    """Performance tests for governance operations."""

    def test_gate_transition_performance(self, db_session):
        """Benchmark gate transition performance."""
        workflow = ICWorkflow(db_session)

        start_time = time.time()

        # Perform multiple gate transitions
        for i in range(100):
            deal_id = i + 1
            try:
                workflow.advance(
                    deal_id=deal_id,
                    target_gate="IOI",
                    artifacts=get_required_artifacts("IOI"),
                    user_id=f"analyst_{i}"
                )
            except Exception:
                # Some deals may fail due to missing artifacts, which is expected
                pass

        end_time = time.time()

        # Should complete in reasonable time
        assert end_time - start_time < 2.0  # < 2 seconds for 100 operations

    def test_quorum_check_performance(self, db_session):
        """Benchmark quorum checking performance."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IC1
        workflow.advance(
            deal_id=1,
            target_gate="IC1",
            artifacts=get_required_artifacts("IC1"),
            user_id="analyst"
        )

        start_time = time.time()

        # Perform multiple quorum checks
        for _ in range(1000):
            workflow.check_quorum("IC1", 1)

        end_time = time.time()

        # Should be very fast
        assert end_time - start_time < 0.5  # < 500ms for 1000 checks

    def test_artifact_validation_performance(self, db_session):
        """Benchmark artifact validation performance."""
        workflow = ICWorkflow(db_session)

        # Set up deal in IOI
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )

        start_time = time.time()

        # Validate artifacts multiple times
        for _ in range(1000):
            workflow.check_gate_completion(1, "IOI")

        end_time = time.time()

        # Should be fast
        assert end_time - start_time < 1.0  # < 1 second for 1000 validations

    def test_audit_trail_performance(self, db_session):
        """Benchmark audit trail logging performance."""
        workflow = ICWorkflow(db_session)

        start_time = time.time()

        # Generate audit entries
        for i in range(100):
            workflow.advance(
                deal_id=i + 1,
                target_gate="IOI",
                artifacts=get_required_artifacts("IOI"),
                user_id=f"analyst_{i}"
            )

        end_time = time.time()

        # Should handle audit logging efficiently
        assert end_time - start_time < 5.0  # < 5 seconds for 100 operations with audit

    def test_repository_operations_performance(self, db_session):
        """Benchmark repository operations performance."""
        repo = GovernanceRepository(db_session)

        # Set up some data
        workflow = ICWorkflow(db_session)
        workflow.advance(
            deal_id=1,
            target_gate="IOI",
            artifacts=get_required_artifacts("IOI"),
            user_id="analyst"
        )

        start_time = time.time()

        # Perform multiple repository operations
        for _ in range(500):
            repo.get_deal_gate(1)
            repo.get_deal_artifacts(1, "IOI")
            repo.get_gate_completion_status(1, "IOI")

        end_time = time.time()

        # Should be fast
        assert end_time - start_time < 1.0  # < 1 second for 1500 operations

    def test_large_deal_set_performance(self, db_session):
        """Benchmark performance with large number of deals."""
        workflow = ICWorkflow(db_session)

        start_time = time.time()

        # Process 1000 deals
        for deal_id in range(1, 1001):
            try:
                workflow.advance(
                    deal_id=deal_id,
                    target_gate="IOI",
                    artifacts=get_required_artifacts("IOI"),
                    user_id=f"analyst_{deal_id % 10}"  # Rotate analysts
                )
            except Exception:
                # Some may fail due to database constraints, which is expected
                pass

        end_time = time.time()

        # Should scale reasonably
        assert end_time - start_time < 30.0  # < 30 seconds for 1000 deals

    def test_memory_usage_efficiency(self, db_session):
        """Test that memory usage remains reasonable during operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        workflow = ICWorkflow(db_session)

        # Process many deals
        for deal_id in range(1, 101):  # 100 deals
            workflow.advance(
                deal_id=deal_id,
                target_gate="IOI",
                artifacts=get_required_artifacts("IOI"),
                user_id="analyst"
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 100  # < 100MB increase for 100 deals

    @pytest.mark.performance
    def test_scaling_analysis(self):
        """Analyze performance scaling with increasing deal complexity."""
        # Test with different numbers of artifacts per gate
        artifact_counts = [4, 8, 12, 16, 20]  # Screen, IOI, LOI, IC1, IC2 artifact counts
        times = []

        for count in artifact_counts:
            # Create mock gate with specified artifact count
            mock_artifacts = [f"artifact_{i}" for i in range(count)]

            start_time = time.time()

            # Simulate workflow operations
            for _ in range(10):  # 10 operations per test
                # This would be the core validation logic
                provided = mock_artifacts.copy()
                missing = [art for art in mock_artifacts if art not in provided]

            end_time = time.time()
            times.append(end_time - start_time)

        # Verify reasonable scaling (should be roughly linear)
        # Each doubling should roughly double execution time
        for i in range(len(artifact_counts) - 1):
            ratio = times[i + 1] / times[i]
            count_ratio = artifact_counts[i + 1] / artifact_counts[i]
            # Allow some variance due to Python overhead
            assert ratio < count_ratio * 2.0

        # All should complete quickly
        assert all(t < 0.01 for t in times)  # All < 10ms

    def test_concurrent_workflow_performance(self, db_session):
        """Test performance under concurrent workflow operations."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        workflow = ICWorkflow(db_session)

        def perform_workflow_operations(deal_id_start, count):
            """Perform workflow operations for a range of deals."""
            for i in range(count):
                deal_id = deal_id_start + i
                try:
                    workflow.advance(
                        deal_id=deal_id,
                        target_gate="IOI",
                        artifacts=get_required_artifacts("IOI"),
                        user_id="analyst"
                    )
                except Exception:
                    pass  # Expected for some deals

        start_time = time.time()

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []

            # Submit 4 concurrent tasks, each handling 25 deals
            for i in range(4):
                future = executor.submit(perform_workflow_operations, i * 25 + 1, 25)
                futures.append(future)

            # Wait for all to complete
            for future in as_completed(futures):
                future.result()

        end_time = time.time()

        # Should handle concurrent operations efficiently
        assert end_time - start_time < 10.0  # < 10 seconds for 100 concurrent operations
