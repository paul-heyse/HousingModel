"""Tests for source data connectors."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from aker_core.connectors import BaseConnector, ConnectorRegistry, DataConnector, get_connector


class TestBaseConnector:
    """Test BaseConnector functionality."""

    def test_base_connector_initialization(self):
        """Test base connector initialization."""
        connector = BaseConnector("test", "https://api.example.com")
        assert connector.name == "test"
        assert connector.base_url == "https://api.example.com"
        assert hasattr(connector, "logger")
        assert hasattr(connector, "session")

    def test_make_request_success(self):
        """Test successful HTTP request."""
        connector = BaseConnector("test", "https://api.example.com")

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"test": "data"}'

        with patch.object(connector.session, "request", return_value=mock_response):
            response = connector._make_request("/test")

            assert response.status_code == 200
            assert response.content == mock_response.content

    def test_make_request_failure(self):
        """Test failed HTTP request."""
        connector = BaseConnector("test", "https://api.example.com")

        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"

        with patch.object(connector.session, "request", return_value=mock_response):
            response = connector._make_request("/test")

            assert response.status_code == 500

    def test_date_range_validation(self):
        """Test date range validation."""
        connector = BaseConnector("test", "https://api.example.com")

        from datetime import date

        today = date.today()

        # Valid range
        assert connector._validate_date_range(today, today) is True

        # Invalid range (start after end)
        assert connector._validate_date_range(today, today.replace(day=today.day - 1)) is False


class TestDataConnector:
    """Test DataConnector functionality."""

    def test_data_connector_initialization(self):
        """Test data connector initialization."""
        schema = {"id": "int64", "name": "string"}
        connector = DataConnector("test", "https://api.example.com", schema)

        assert connector.name == "test"
        assert connector.output_schema == schema

    def test_fetch_data_with_dataframe(self):
        """Test fetch_data with DataFrame result."""
        schema = {"id": "int64", "name": "string"}
        connector = DataConnector("test", "https://api.example.com", schema)

        # Mock _fetch_raw_data to return DataFrame
        test_df = pd.DataFrame({"id": [1, 2], "name": ["test1", "test2"]})
        connector._fetch_raw_data = MagicMock(return_value=test_df)

        result = connector.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "id" in result.columns
        assert "name" in result.columns

    def test_fetch_data_with_dict(self):
        """Test fetch_data with dictionary result."""
        schema = {"id": "int64", "name": "string"}
        connector = DataConnector("test", "https://api.example.com", schema)

        # Mock _fetch_raw_data to return dict
        test_data = {"id": [1, 2], "name": ["test1", "test2"]}
        connector._fetch_raw_data = MagicMock(return_value=test_data)

        result = connector.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_schema_validation_missing_columns(self):
        """Test schema validation with missing columns."""
        schema = {"id": "int64", "name": "string", "missing": "string"}
        connector = DataConnector("test", "https://api.example.com", schema)

        # Mock _fetch_raw_data to return DataFrame without required column
        test_df = pd.DataFrame({"id": [1, 2], "name": ["test1", "test2"]})
        connector._fetch_raw_data = MagicMock(return_value=test_df)

        with pytest.raises(ValueError, match="Missing expected columns"):
            connector.fetch_data()

    def test_date_range_validation_invalid(self):
        """Test invalid date range handling."""
        schema = {"id": "int64", "name": "string"}
        connector = DataConnector("test", "https://api.example.com", schema)

        from datetime import date

        today = date.today()

        with pytest.raises(ValueError, match="Invalid date range"):
            connector.fetch_data(start_date=today, end_date=today.replace(day=today.day - 1))


class TestConnectorRegistry:
    """Test connector registry functionality."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ConnectorRegistry()
        assert registry.connectors is not None
        assert registry.logger is not None

    def test_register_connector(self):
        """Test connector registration."""
        registry = ConnectorRegistry()

        # Create a mock connector
        class MockConnector(BaseConnector):
            def fetch_data(self, start_date=None, end_date=None, **kwargs):
                return pd.DataFrame({"test": [1, 2]})

        registry.register_connector("test", MockConnector)
        assert "test" in registry.connectors
        assert registry.connectors["test"] == MockConnector

    def test_get_connector(self):
        """Test getting connector from registry."""
        registry = ConnectorRegistry()

        # Register a mock connector
        class MockConnector(BaseConnector):
            def fetch_data(self, start_date=None, end_date=None, **kwargs):
                return pd.DataFrame({"test": [1, 2]})

        registry.register_connector("test", MockConnector)

        connector = registry.get_connector("test")
        assert isinstance(connector, MockConnector)
        assert connector.name == "test"

    def test_get_connector_not_found(self):
        """Test getting non-existent connector."""
        registry = ConnectorRegistry()

        with pytest.raises(ValueError, match="Connector 'nonexistent' not found"):
            registry.get_connector("nonexistent")

    def test_list_connectors(self):
        """Test listing registered connectors."""
        registry = ConnectorRegistry()

        # Should have at least the basic connectors
        connectors = registry.list_connectors()
        assert isinstance(connectors, list)

    def test_has_connector(self):
        """Test checking if connector exists."""
        registry = ConnectorRegistry()

        assert registry.has_connector("nonexistent") is False

        # Register a connector
        class MockConnector(BaseConnector):
            def fetch_data(self, start_date=None, end_date=None, **kwargs):
                return pd.DataFrame({"test": [1, 2]})

        registry.register_connector("test", MockConnector)
        assert registry.has_connector("test") is True


class TestGlobalRegistry:
    """Test global registry functions."""

    def test_get_registry_singleton(self):
        """Test that get_registry returns a singleton."""
        from aker_core.connectors import get_registry

        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_register_connector_global(self):
        """Test global connector registration."""
        from aker_core.connectors import register_connector

        # Create a mock connector
        class MockConnector(BaseConnector):
            def fetch_data(self, start_date=None, end_date=None, **kwargs):
                return pd.DataFrame({"test": [1, 2]})

        register_connector("global_test", MockConnector)

        # Should be able to get it
        connector = get_connector("global_test")
        assert isinstance(connector, MockConnector)

    def test_get_connector_global(self):
        """Test global connector retrieval."""

        # Should be able to get the connector we just registered
        connector = get_connector("global_test")
        assert connector is not None

    def test_list_connectors_global(self):
        """Test global connector listing."""
        from aker_core.connectors import list_connectors

        connectors = list_connectors()
        assert isinstance(connectors, list)
        assert "global_test" in connectors
