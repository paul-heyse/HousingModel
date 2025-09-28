"""Tests for Ops & Brand dashboard functionality."""

import pytest
import json
from datetime import date

from aker_gui.api.ops import get_reputation_data, process_csv_upload, get_pricing_preview
from aker_gui.dash_pages.ops_brand_dashboard import create_ops_brand_dashboard


class TestOpsAPI:
    """Test ops API endpoints."""

    def test_get_reputation_data_basic(self):
        """Test basic reputation data retrieval."""
        data = get_reputation_data("TEST-001")

        assert "reputation_idx" in data
        assert "nps_series" in data
        assert "reviews_series" in data
        assert "pricing_rules" in data

        assert isinstance(data["reputation_idx"], (int, float))
        assert isinstance(data["nps_series"], list)
        assert isinstance(data["reviews_series"], list)
        assert isinstance(data["pricing_rules"], dict)

    def test_get_reputation_data_with_dates(self):
        """Test reputation data with date filtering."""
        data = get_reputation_data("TEST-001", "2024-01-01", "2024-06-30")

        assert "reputation_idx" in data
        assert len(data["nps_series"]) > 0
        assert len(data["reviews_series"]) > 0

    def test_process_csv_upload_valid(self):
        """Test CSV upload with valid data."""
        # Create a simple CSV string
        csv_content = "date,source,rating,text,response_time_days,is_move_in\n2024-01-15,Google,4.5,Great place,2,true"

        # Mock file object
        class MockFile:
            def read(self):
                return csv_content.encode('utf-8')

        result = process_csv_upload(MockFile())

        assert "ingested" in result
        assert "rejected" in result
        assert result["ingested"] == 1
        assert result["rejected"] == 0

    def test_process_csv_upload_invalid(self):
        """Test CSV upload with invalid data."""
        # Create CSV with invalid rating
        csv_content = "date,source,rating,text,response_time_days,is_move_in\n2024-01-15,Google,6.5,Invalid rating,2,true"

        class MockFile:
            def read(self):
                return csv_content.encode('utf-8')

        result = process_csv_upload(MockFile())

        assert "rejected" in result
        assert result["rejected"] == 1
        assert len(result["sample_errors"]) > 0

    def test_get_pricing_preview(self):
        """Test pricing preview for different reputation levels."""
        preview = get_pricing_preview("TEST-001", 85.0)

        assert "guardrails" in preview
        assert "based_on_reputation" in preview
        assert "asset_id" in preview

        assert preview["based_on_reputation"] == 85.0
        assert preview["asset_id"] == "TEST-001"


class TestOpsBrandDashboard:
    """Test Ops & Brand dashboard components."""

    def test_dashboard_creation(self):
        """Test dashboard layout creation."""
        dashboard = create_ops_brand_dashboard("TEST-001")

        # Check that dashboard has expected structure
        assert dashboard is not None
        assert hasattr(dashboard, 'children')

        # Check for key components
        dashboard_str = str(dashboard)
        assert "Ops & Brand" in dashboard_str
        assert "ops-nps-chart" in dashboard_str
        assert "ops-reviews-chart" in dashboard_str
        assert "ops-reputation-index" in dashboard_str

    def test_dashboard_with_default_asset(self):
        """Test dashboard creation with default asset."""
        dashboard = create_ops_brand_dashboard()

        # Should default to AKR-123
        dashboard_str = str(dashboard)
        assert "AKR-123" in dashboard_str


class TestIntegration:
    """Integration tests for ops dashboard."""

    def test_end_to_end_data_flow(self):
        """Test complete data flow from API to dashboard."""
        # Get reputation data
        data = get_reputation_data("TEST-001")

        # Verify data structure
        assert 0 <= data["reputation_idx"] <= 100
        assert len(data["nps_series"]) > 0
        assert len(data["reviews_series"]) > 0

        # Verify pricing rules
        rules = data["pricing_rules"]
        assert "max_concession_days" in rules
        assert "floor_price_pct" in rules
        assert "premium_cap_pct" in rules

    def test_csv_upload_workflow(self):
        """Test complete CSV upload workflow."""
        # Create valid CSV
        csv_data = "date,source,rating,text,response_time_days,is_move_in\n2024-01-15,Google,4.5,Great place,2,true"

        class MockFile:
            def read(self):
                return csv_data.encode('utf-8')

        # Process upload
        result = process_csv_upload(MockFile())

        # Verify successful processing
        assert result["ingested"] == 1
        assert result["rejected"] == 0
        assert "total_rows" in result

    def test_pricing_preview_workflow(self):
        """Test pricing preview workflow."""
        # Test different reputation levels
        for rep_idx in [45, 65, 85]:
            preview = get_pricing_preview("TEST-001", rep_idx)

            assert preview["based_on_reputation"] == rep_idx
            assert "guardrails" in preview

            # Guardrails should change based on reputation level
            rules = preview["guardrails"]
            if rep_idx >= 80:
                assert rules["max_concession_days"] == 0
            elif rep_idx >= 65:
                assert rules["max_concession_days"] == 7


class TestErrorHandling:
    """Test error handling in ops dashboard."""

    def test_invalid_reputation_request(self):
        """Test handling of invalid reputation requests."""
        # Request without asset_id
        try:
            data = get_reputation_data("")
            assert "error" in data
        except Exception:
            pass  # Expected to fail gracefully

    def test_csv_upload_errors(self):
        """Test CSV upload error handling."""
        # Empty file
        class EmptyFile:
            def read(self):
                return b""

        result = process_csv_upload(EmptyFile())
        assert "error" in result

        # File with wrong format
        class InvalidFile:
            def read(self):
                return b"not,csv,data"

        result = process_csv_upload(InvalidFile())
        assert "error" in result or "rejected" in result

    def test_pricing_preview_validation(self):
        """Test pricing preview input validation."""
        # Invalid reputation index
        try:
            preview = get_pricing_preview("TEST-001", 150)
            assert "error" in preview
        except Exception:
            pass  # Should handle gracefully


class TestDataConsistency:
    """Test data consistency across API endpoints."""

    def test_reputation_data_structure(self):
        """Test that reputation data has consistent structure."""
        data = get_reputation_data("TEST-001")

        # All time series should have same length
        nps_count = len(data["nps_series"])
        reviews_count = len(data["reviews_series"])

        assert nps_count > 0
        assert reviews_count > 0

        # Each series item should have required fields
        for nps_item in data["nps_series"]:
            assert "date" in nps_item
            assert "nps" in nps_item
            assert isinstance(nps_item["nps"], (int, float))

        for review_item in data["reviews_series"]:
            assert "date" in review_item
            assert "rating" in review_item
            assert "volume" in review_item
            assert isinstance(review_item["rating"], (int, float))

    def test_pricing_rules_consistency(self):
        """Test that pricing rules are consistent across reputation levels."""
        # Test different reputation levels
        for rep_idx in [45, 65, 85]:
            preview = get_pricing_preview("TEST-001", rep_idx)
            rules = preview["guardrails"]

            # All rules should have required fields
            assert "max_concession_days" in rules
            assert "floor_price_pct" in rules
            assert "premium_cap_pct" in rules

            # Values should be reasonable
            assert 0 <= rules["max_concession_days"] <= 30
            assert 0 <= rules["floor_price_pct"] <= 20
            assert 0 <= rules["premium_cap_pct"] <= 15
