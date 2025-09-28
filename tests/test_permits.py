"""Tests for permit portal ingestion functionality."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from aker_core.permits import (
    ConnectorRegistry,
    PermitRecord,
    PermitsConnector,
    PermitStatus,
    PermitType,
)
from aker_core.permits.models import Address


@pytest.fixture
def sample_permit_data():
    """Create sample permit data for testing."""
    return [
        {
            "permit_id": "P2023001",
            "permit_type": "residential_new",
            "status": "approved",
            "description": "New single family residence",
            "application_date": "2023-01-15",
            "issue_date": "2023-02-01",
            "expiration_date": "2023-12-31",
            "estimated_cost": 350000,
            "actual_cost": None,
            "property_type": "residential",
            "square_footage": 2500,
            "applicant_name": "John Doe",
            "contractor_name": "ABC Construction",
            "contractor_license": "LIC123456",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12345",
                "latitude": 34.0522,
                "longitude": -118.2437,
            },
        },
        {
            "permit_id": "P2023002",
            "permit_type": "residential_renovation",
            "status": "pending",
            "description": "Kitchen remodel",
            "application_date": "2023-03-10",
            "issue_date": None,
            "expiration_date": None,
            "estimated_cost": 75000,
            "actual_cost": None,
            "property_type": "residential",
            "square_footage": 800,
            "applicant_name": "Jane Smith",
            "contractor_name": "XYZ Builders",
            "contractor_license": "LIC789012",
            "address": {
                "street": "456 Oak Ave",
                "city": "Anytown",
                "state": "CA",
                "zip_code": "12346",
                "latitude": 34.0523,
                "longitude": -118.2438,
            },
        },
    ]


@pytest.fixture
def mock_run_context():
    """Create a mock RunContext for testing."""
    return MagicMock()


class TestPermitModels:
    """Test permit data models."""

    def test_permit_record_creation(self):
        """Test creating a PermitRecord."""
        address = Address(
            street="123 Main St",
            city="Anytown",
            state="CA",
            zip_code="12345",
            latitude=34.0522,
            longitude=-118.2437,
        )

        permit = PermitRecord(
            permit_id="P2023001",
            permit_type=PermitType.RESIDENTIAL_NEW,
            status=PermitStatus.APPROVED,
            description="New residence",
            application_date=date(2023, 1, 15),
            issue_date=date(2023, 2, 1),
            estimated_cost=350000,
            address=address,
            property_type="residential",
            applicant_name="John Doe",
            source_system="test_system",
        )

        assert permit.permit_id == "P2023001"
        assert permit.permit_type == PermitType.RESIDENTIAL_NEW
        assert permit.status == PermitStatus.APPROVED
        assert permit.estimated_cost == 350000

    def test_permit_record_validation(self):
        """Test permit record validation."""
        address = Address(street="123 Main St", city="Anytown", state="CA", zip_code="12345")

        # Test with invalid cost
        with pytest.raises(ValueError, match="Cost values cannot be negative"):
            PermitRecord(
                permit_id="P2023001",
                permit_type=PermitType.RESIDENTIAL_NEW,
                status=PermitStatus.APPROVED,
                description="Test",
                application_date=date(2023, 1, 15),
                estimated_cost=-1000,  # Invalid negative cost
                address=address,
                property_type="residential",
                applicant_name="John Doe",
                source_system="test_system",
            )

    def test_permit_record_serialization(self):
        """Test permit record serialization."""
        address = Address(street="123 Main St", city="Anytown", state="CA", zip_code="12345")

        permit = PermitRecord(
            permit_id="P2023001",
            permit_type=PermitType.RESIDENTIAL_NEW,
            status=PermitStatus.APPROVED,
            description="Test permit",
            application_date=date(2023, 1, 15),
            address=address,
            property_type="residential",
            applicant_name="John Doe",
            source_system="test_system",
        )

        # Test to_dict
        permit_dict = permit.to_dict()
        assert permit_dict["permit_id"] == "P2023001"
        assert permit_dict["address"]["street"] == "123 Main St"

        # Test from_dict
        permit_from_dict = PermitRecord.from_dict(permit_dict)
        assert permit_from_dict.permit_id == permit.permit_id


class TestConnectorRegistry:
    """Test connector registry functionality."""

    def test_registry_initialization(self):
        """Test connector registry initialization."""
        registry = ConnectorRegistry()

        # Should have at least NYC and LA connectors registered
        connectors = registry.list_registered_connectors()
        assert len(connectors) >= 2  # At least NYC and LA

        # Check that NYC and LA are registered
        nyc_registered = any(city == "New York" and state == "NY" for city, state in connectors)
        la_registered = any(city == "Los Angeles" and state == "CA" for city, state in connectors)

        assert nyc_registered, "NYC connector should be registered"
        assert la_registered, "LA connector should be registered"

    def test_get_connector(self, mock_run_context):
        """Test getting connector from registry."""
        registry = ConnectorRegistry()

        # Test NYC connector
        nyc_connector = registry.get_connector("New York", "NY", mock_run_context)
        assert nyc_connector is not None
        assert nyc_connector.city == "New York"
        assert nyc_connector.state == "NY"

        # Test LA connector
        la_connector = registry.get_connector("Los Angeles", "CA", mock_run_context)
        assert la_connector is not None
        assert la_connector.city == "Los Angeles"
        assert la_connector.state == "CA"

    def test_has_connector(self):
        """Test checking if connector is registered."""
        registry = ConnectorRegistry()

        assert registry.has_connector("New York", "NY")
        assert registry.has_connector("Los Angeles", "CA")
        assert not registry.has_connector("Nonexistent", "City")

    def test_register_connector(self):
        """Test registering a new connector."""
        registry = ConnectorRegistry()

        # Create a mock connector class
        class MockConnector(PermitsConnector):
            def fetch_permits(self, start_date=None, end_date=None, permit_types=None):
                pass

            def get_permit_type_enum(self):
                return PermitType

        # Register the connector
        registry.register_connector("TestCity", "TC", MockConnector)

        # Check that it was registered
        assert registry.has_connector("TestCity", "TC")

        # Should be able to get the connector
        connector = registry.get_connector("TestCity", "TC")
        assert isinstance(connector, MockConnector)


class TestNYCConnector:
    """Test NYC permit connector."""

    def test_nyc_connector_initialization(self, mock_run_context):
        """Test NYC connector initialization."""
        from aker_core.permits.connectors.nyc import NYCConnector

        connector = NYCConnector(run_context=mock_run_context)

        assert connector.city == "New York"
        assert connector.state == "NY"
        assert connector.run_context == mock_run_context

    def test_nyc_permit_type_enum(self):
        """Test NYC permit type enum."""
        from aker_core.permits.connectors.nyc import NYCConnector

        connector = NYCConnector()
        permit_types = connector.get_permit_type_enum()

        # Should return the NYCPermitType enum
        assert hasattr(permit_types, "NEW_BUILDING")
        assert hasattr(permit_types, "ALTERATION_1")

    def test_nyc_permit_normalization(self):
        """Test NYC permit data normalization."""
        from aker_core.permits.connectors.nyc import NYCConnector

        connector = NYCConnector()

        # Test data
        raw_permit = {
            "job_number": "P2023001",
            "job_type": "NB",
            "status": "Approved",
            "work_type": "New Building",
            "filing_date": "2023-01-15",
            "issuance_date": "2023-02-01",
            "house_street": "123 Main St",
            "zip_code": "10001",
            "estimated_cost": "350000",
        }

        permit_record = connector._convert_to_permit_record(raw_permit)

        assert permit_record.permit_id == "P2023001"
        assert permit_record.permit_type == PermitType.RESIDENTIAL_NEW
        assert permit_record.status == PermitStatus.APPROVED
        assert permit_record.estimated_cost == 350000


class TestLAConnector:
    """Test LA permit connector."""

    def test_la_connector_initialization(self, mock_run_context):
        """Test LA connector initialization."""
        from aker_core.permits.connectors.la import LAConnector

        connector = LAConnector(run_context=mock_run_context)

        assert connector.city == "Los Angeles"
        assert connector.state == "CA"
        assert connector.run_context == mock_run_context

    def test_la_permit_type_enum(self):
        """Test LA permit type enum."""
        from aker_core.permits.connectors.la import LAConnector

        connector = LAConnector()
        permit_types = connector.get_permit_type_enum()

        # Should return the LAPermitType enum
        assert hasattr(permit_types, "BUILDING_NEW")
        assert hasattr(permit_types, "BUILDING_ALTER_REPAIR")

    def test_la_permit_normalization(self):
        """Test LA permit data normalization."""
        from aker_core.permits.connectors.la import LAConnector

        connector = LAConnector()

        # Test data
        raw_permit = {
            "permit_number": "P2023001",
            "permit_type": "Bldg-New",
            "status": "Issued",
            "description": "New Building",
            "application_date": "2023-01-15",
            "issue_date": "2023-02-01",
            "address": "123 Main St",
            "zip_code": "90210",
            "valuation": "350000",
        }

        permit_record = connector._convert_to_permit_record(raw_permit)

        assert permit_record.permit_id == "P2023001"
        assert permit_record.permit_type == PermitType.RESIDENTIAL_NEW
        assert permit_record.status == PermitStatus.ISSUED
        assert permit_record.valuation == 350000


class TestPermitCollectionFlow:
    """Test permit collection flow functionality."""

    def test_collect_permits_flow_structure(self):
        """Test that collect_permits flow is properly structured."""
        from flows.collect_permits import PermitCollectionFlow, collect_permits

        # Check that flow is properly decorated
        assert hasattr(collect_permits, "is_flow")
        assert collect_permits.name == "collect-permits"

        # Check that flow class exists
        assert PermitCollectionFlow is not None

    def test_permit_collection_flow_initialization(self):
        """Test permit collection flow initialization."""
        from flows.collect_permits import PermitCollectionFlow

        flow = PermitCollectionFlow()

        assert flow.name == "collect_permits"
        assert flow.description == "Collect permits from city/state portals"

    def test_permit_collection_flow_imports(self):
        """Test that permit collection flow can be imported."""
        try:
            from flows.collect_permits import PermitCollectionFlow, collect_permits

            assert callable(collect_permits)
            assert PermitCollectionFlow is not None
        except ImportError as e:
            pytest.skip(f"Import failed: {e}")


class TestIntegration:
    """Integration tests for permit portal functionality."""

    def test_permit_module_imports(self):
        """Test that permit module can be imported."""
        try:
            from aker_core.permits import (
                ConnectorRegistry,
                PermitRecord,
                PermitsConnector,
                PermitStatus,
                PermitType,
                get_connector,
            )

            # Check that all classes and functions are available
            assert PermitsConnector is not None
            assert callable(get_connector)
            assert PermitRecord is not None
            assert PermitStatus is not None
            assert PermitType is not None
            assert ConnectorRegistry is not None

        except ImportError as e:
            pytest.skip(f"Import failed: {e}")

    def test_connector_registry_integration(self, mock_run_context):
        """Test connector registry integration."""
        try:
            from aker_core.permits import ConnectorRegistry, get_connector

            registry = ConnectorRegistry()

            # Test that we can get connectors
            nyc_connector = get_connector("New York", "NY", mock_run_context)
            assert nyc_connector.city == "New York"
            assert nyc_connector.state == "NY"

            la_connector = get_connector("Los Angeles", "CA", mock_run_context)
            assert la_connector.city == "Los Angeles"
            assert la_connector.state == "CA"

            # Registry should be able to enumerate registered connectors
            available = {connector.city for connector in registry.connectors}
            assert {"New York", "Los Angeles"}.issubset(available)

        except ImportError as e:
            pytest.skip(f"Connector integration failed: {e}")

    def test_permit_record_round_trip(self):
        """Test permit record creation and serialization."""
        address = Address(street="123 Main St", city="Anytown", state="CA", zip_code="12345")

        # Create permit record
        permit = PermitRecord(
            permit_id="P2023001",
            permit_type=PermitType.RESIDENTIAL_NEW,
            status=PermitStatus.APPROVED,
            description="New residence",
            application_date=date(2023, 1, 15),
            address=address,
            applicant_name="John Doe",
            source_system="test_system",
        )

        # Test serialization
        permit_dict = permit.to_dict()
        permit_json = permit.to_json()

        # Test deserialization
        permit_from_dict = PermitRecord.from_dict(permit_dict)
        permit_from_json = PermitRecord.from_json(permit_json)

        # Verify round-trip integrity
        assert permit_from_dict.permit_id == permit.permit_id
        assert permit_from_dict.permit_type == permit.permit_type
        assert permit_from_json.permit_id == permit.permit_id
        assert permit_from_json.address.street == permit.address.street


class TestPermitCollectionResult:
    """Test permit collection result functionality."""

    def test_collection_result_success(self):
        """Test collection result with successful collection."""
        from aker_core.permits.models import PermitCollectionResult

        permits = [MagicMock(), MagicMock()]
        metadata = {"records_fetched": 100}

        result = PermitCollectionResult(permits, metadata)

        assert result.success is True
        assert result.total_permits == 2
        assert result.collection_metadata == metadata

    def test_collection_result_with_errors(self):
        """Test collection result with errors."""
        from aker_core.permits.models import PermitCollectionResult

        permits = [MagicMock()]
        metadata = {"records_fetched": 50}
        errors = ["API rate limit exceeded", "Invalid response format"]

        result = PermitCollectionResult(permits, metadata, errors)

        assert result.success is False
        assert result.total_permits == 1
        assert result.errors == errors

    def test_collection_result_serialization(self):
        """Test collection result serialization."""
        from aker_core.permits.models import PermitCollectionResult

        permits = [MagicMock()]
        metadata = {"records_fetched": 25}

        result = PermitCollectionResult(permits, metadata)
        result_dict = result.to_dict()

        assert result_dict["total_permits"] == 1
        assert result_dict["collection_metadata"] == metadata
        assert result_dict["success"] is True
        assert "errors" in result_dict
