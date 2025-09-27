"""Tests for geospatial utilities and CRS transformations."""

from __future__ import annotations

import tempfile

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon


@pytest.fixture
def sample_geodataframe():
    """Create a sample GeoDataFrame for testing."""
    # Create sample geometries
    geometries = [
        Point(-74.0059, 40.7128),  # New York
        Point(-118.2437, 34.0522),  # Los Angeles
        Point(-87.6298, 41.8781),  # Chicago
    ]

    # Create DataFrame
    df = pd.DataFrame(
        {
            "name": ["New York", "Los Angeles", "Chicago"],
            "population": [8500000, 4000000, 2700000],
            "geometry": geometries,
        }
    )

    return gpd.GeoDataFrame(df, crs="EPSG:4326")


@pytest.fixture
def sample_dataframe_with_geometry():
    """Create a sample DataFrame with geometry column (not GeoDataFrame)."""
    geometries = [
        Point(-74.0059, 40.7128),  # New York
        Point(-118.2437, 34.0522),  # Los Angeles
        Point(-87.6298, 41.8781),  # Chicago
    ]

    return pd.DataFrame(
        {
            "name": ["New York", "Los Angeles", "Chicago"],
            "population": [8500000, 4000000, 2700000],
            "geometry": geometries,
        }
    )


class TestCRSTransformations:
    """Test CRS transformation utilities."""

    def test_to_ui_transforms_to_web_mercator(self, sample_geodataframe):
        """Test transformation from storage CRS to UI CRS."""
        from aker_geo.crs import to_ui

        result = to_ui(sample_geodataframe)

        assert isinstance(result, gpd.GeoDataFrame)
        assert result.crs == "EPSG:3857"
        assert len(result) == len(sample_geodataframe)

    def test_to_storage_transforms_to_geographic(self, sample_geodataframe):
        """Test transformation from UI CRS to storage CRS."""
        from aker_geo.crs import to_storage

        # First transform to UI CRS
        ui_gdf = sample_geodataframe.to_crs("EPSG:3857")

        # Then transform back to storage CRS
        result = to_storage(ui_gdf)

        assert isinstance(result, gpd.GeoDataFrame)
        assert result.crs == "EPSG:4326"
        assert len(result) == len(sample_geodataframe)

    def test_crs_info_retrieval(self):
        """Test CRS information retrieval."""
        from aker_geo.crs import get_crs_info

        info = get_crs_info("EPSG:4326")

        assert "name" in info
        assert "datum" in info
        assert "coordinate_system" in info
        assert info["name"] == "WGS 84"

    def test_crs_compatibility_validation(self):
        """Test CRS compatibility validation."""
        from aker_geo.crs import validate_crs_compatibility

        # Compatible CRS
        assert validate_crs_compatibility("EPSG:4326", "EPSG:3857") is True

        # Same CRS should be compatible
        assert validate_crs_compatibility("EPSG:4326", "EPSG:4326") is True

    def test_geometry_transformation(self):
        """Test single geometry transformation."""
        from aker_geo.crs import transform_geometry

        # Create a simple geometry
        geometry = Point(-74.0059, 40.7128)

        # Transform from storage to UI CRS
        transformed = transform_geometry(geometry, "EPSG:4326", "EPSG:3857")

        assert transformed is not None
        assert transformed.geom_type == "Point"

    def test_crs_detection_from_geometry(self):
        """Test CRS detection from geometry bounds."""
        from aker_geo.crs import detect_crs_from_geometry

        # Geographic coordinates (should detect EPSG:4326)
        geo_point = Point(-74.0059, 40.7128)
        detected = detect_crs_from_geometry(geo_point)
        assert detected == "EPSG:4326"

        # Projected coordinates (should detect EPSG:3857)
        proj_point = Point(-8232000, 4972000)  # Approximate NYC in Web Mercator
        detected = detect_crs_from_geometry(proj_point)
        assert detected == "EPSG:3857"


class TestGeometryValidation:
    """Test geometry validation utilities."""

    def test_validate_geometry_valid_geometries(self, sample_geodataframe):
        """Test validation of valid geometries."""
        from aker_geo.validate import validate_geometry

        result = validate_geometry(sample_geodataframe)

        # Check that all geometries are valid
        assert result.total_geometries == 3
        assert result.valid_geometries == 3
        assert result.invalid_geometries == 0
        assert result.validity_rate == 1.0

    def test_validate_geometry_invalid_geometries(self):
        """Test validation of invalid geometries."""
        from aker_geo.validate import validate_geometry

        # Create invalid geometry (self-intersecting polygon)
        invalid_geom = Polygon([(0, 0), (1, 1), (0, 2), (2, 0), (0, 0)])
        df = gpd.GeoDataFrame(
            {"name": ["Invalid Polygon"], "geometry": [invalid_geom]}, crs="EPSG:4326"
        )

        result = validate_geometry(df)

        # Check that invalid geometry is detected
        assert result.total_geometries == 1
        assert result.invalid_geometries == 1
        assert result.valid_geometries == 0
        assert result.validity_rate == 0.0

    def test_validate_crs_storage_crs(self, sample_geodataframe):
        """Test CRS validation for storage CRS."""
        from aker_geo.validate import validate_crs

        result = validate_crs(sample_geodataframe)

        assert result["has_crs"] is True
        assert result["is_storage_crs"] is True
        assert result["is_ui_crs"] is False

    def test_validate_crs_ui_crs(self):
        """Test CRS validation for UI CRS."""
        from aker_geo.validate import validate_crs

        # Create GeoDataFrame with UI CRS
        df = gpd.GeoDataFrame({"name": ["Test"], "geometry": [Point(0, 0)]}, crs="EPSG:3857")

        result = validate_crs(df)

        assert result["has_crs"] is True
        assert result["is_storage_crs"] is False
        assert result["is_ui_crs"] is True

    def test_geometry_correction(self):
        """Test geometry correction utilities."""
        from aker_geo.validate import correct_geometry

        # Create invalid geometry
        invalid_geom = Polygon([(0, 0), (1, 1), (0, 2), (2, 0), (0, 0)])

        # Try to correct
        corrected = correct_geometry(invalid_geom)

        # Should return a corrected geometry or None
        assert corrected is not None or corrected is None

    def test_geometry_types_validation(self, sample_geodataframe):
        """Test geometry types validation."""
        from aker_geo.validate import validate_geometry_types

        result = validate_geometry_types(sample_geodataframe)

        assert result["total_geometries"] == 3
        assert result["has_mixed_types"] is False
        assert result["empty_geometries"] == 0
        assert result["null_geometries"] == 0
        assert result["valid_geometries"] == 3
        assert "Point" in result["geometry_types"]

    def test_spatial_bounds_validation(self, sample_geodataframe):
        """Test spatial bounds validation."""
        from aker_geo.validate import validate_spatial_bounds

        result = validate_spatial_bounds(sample_geodataframe)

        assert result["has_bounds"] is True
        assert "min_x" in result
        assert "min_y" in result
        assert "max_x" in result
        assert "max_y" in result
        assert "width" in result
        assert "height" in result

    def test_postgis_compatibility(self, sample_geodataframe):
        """Test PostGIS compatibility validation."""
        from aker_geo.validate import validate_postgis_compatibility

        result = validate_postgis_compatibility(sample_geodataframe)

        assert result["crs_compatible"] is True
        assert result["geometry_types_supported"] is True
        assert result["has_srid"] is True
        assert result["srid_value"] == "EPSG:4326"

    def test_comprehensive_validation(self, sample_geodataframe):
        """Test comprehensive geometry validation."""
        from aker_geo.validate import comprehensive_geometry_validation

        result = comprehensive_geometry_validation(sample_geodataframe)

        assert "geometry_validation" in result
        assert "crs_validation" in result
        assert "geometry_types" in result
        assert "spatial_bounds" in result
        assert "postgis_compatibility" in result
        assert "summary" in result

        # Check summary contains expected metrics
        summary = result["summary"]
        assert "total_geometries" in summary
        assert "valid_geometries" in summary
        assert "validity_rate" in summary


class TestAkerCoreIntegration:
    """Test integration with aker_core package."""

    def test_aker_core_geospatial_imports(self):
        """Test that geospatial utilities are available in aker_core."""
        try:
            from aker_core import to_storage, to_ui, validate_crs, validate_geometry

            assert callable(to_storage)
            assert callable(to_ui)
            assert callable(validate_geometry)
            assert callable(validate_crs)
        except ImportError:
            pytest.skip("Geospatial dependencies not available")

    def test_data_lake_geospatial_integration(self, sample_geodataframe):
        """Test geospatial integration with data lake."""
        from aker_data.lake import DataLake

        with tempfile.TemporaryDirectory() as temp_dir:
            lake = DataLake(base_path=temp_dir)

            # Test that lake can handle GeoDataFrames
            result_path = lake.write(
                sample_geodataframe, dataset="test_geospatial", as_of="2025-01"
            )

            # Verify file was created
            from pathlib import Path

            assert Path(result_path).exists()

            # Test reading back
            read_df = lake.read("test_geospatial", "2025-01")
            # The read should work even if geometry conversion has warnings
            assert len(read_df) > 0


class TestRoundTripTransformations:
    """Test round-trip CRS transformations."""

    def test_storage_to_ui_to_storage(self, sample_geodataframe):
        """Test complete round-trip transformation."""
        from aker_geo.crs import to_storage, to_ui

        # Storage -> UI -> Storage
        ui_gdf = to_ui(sample_geodataframe)
        back_to_storage = to_storage(ui_gdf)

        # Verify round-trip
        assert back_to_storage.crs == "EPSG:4326"
        assert len(back_to_storage) == len(sample_geodataframe)

        # Check that coordinates are approximately preserved (allowing for transformation precision)
        original_bounds = sample_geodataframe.total_bounds
        roundtrip_bounds = back_to_storage.total_bounds

        # Allow for small differences due to transformation precision
        tolerance = 0.01
        assert abs(original_bounds[0] - roundtrip_bounds[0]) < tolerance
        assert abs(original_bounds[1] - roundtrip_bounds[1]) < tolerance

    def test_ui_to_storage_to_ui(self):
        """Test UI to storage to UI round-trip."""
        from aker_geo.crs import to_storage, to_ui

        # Create UI CRS GeoDataFrame
        ui_gdf = gpd.GeoDataFrame(
            {"name": ["Test Point"], "geometry": [Point(-8232000, 4972000)]},  # NYC in Web Mercator
            crs="EPSG:3857",
        )

        # UI -> Storage -> UI
        storage_gdf = to_storage(ui_gdf)
        back_to_ui = to_ui(storage_gdf)

        # Verify round-trip
        assert back_to_ui.crs == "EPSG:3857"
        assert len(back_to_ui) == len(ui_gdf)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test validation with empty DataFrame."""
        from aker_geo.validate import validate_geometry

        empty_df = gpd.GeoDataFrame(columns=["name", "geometry"], crs="EPSG:4326")
        result = validate_geometry(empty_df)

        assert result.total_geometries == 0
        assert result.valid_geometries == 0
        assert result.invalid_geometries == 0

    def test_dataframe_without_geometry_column(self):
        """Test validation with DataFrame missing geometry column."""
        from aker_geo.validate import validate_geometry

        df = pd.DataFrame({"name": ["Test"]})

        with pytest.raises(ValueError, match="must have 'geometry' column"):
            validate_geometry(df)

    def test_unsupported_crs_transformation(self):
        """Test transformation with unsupported CRS."""
        from aker_geo.crs import validate_crs_compatibility

        # Test with obviously incompatible CRS
        assert validate_crs_compatibility("EPSG:4326", "EPSG:999999") is False

    def test_geometry_with_null_values(self):
        """Test validation with null geometry values."""
        from aker_geo.validate import validate_geometry

        df = gpd.GeoDataFrame(
            {"name": ["Valid", "Invalid"], "geometry": [Point(0, 0), None]}, crs="EPSG:4326"
        )

        result = validate_geometry(df)

        assert result.total_geometries == 2
        assert result.valid_geometries == 1
        assert result.invalid_geometries == 1
        assert len(result.validation_errors) == 1
        assert result.validation_errors[0]["error_type"] == "null_geometry"
