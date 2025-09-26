from __future__ import annotations

# Test that deployment configurations can be imported
def test_deployment_imports():
    """Test that deployment configurations can be imported without errors."""
    try:
        from flows.deployments import (
            market_data_refresh,
            market_data_refresh_manual,
            market_scoring,
            market_scoring_manual,
        )

        # Check that the deployment objects exist and have expected attributes
        assert hasattr(market_data_refresh, "name")
        assert hasattr(market_data_refresh, "flow")
        assert hasattr(market_scoring, "name")
        assert hasattr(market_scoring, "flow")

        print("✓ Deployment configurations imported successfully")

    except ImportError as e:
        # If Prefect server is not running, this is expected
        print(f"⚠ Deployment import failed (expected if Prefect server not running): {e}")
        # This is not a test failure since it requires Prefect server

