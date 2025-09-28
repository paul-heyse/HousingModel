"""Tests for the Parquet data lake functionality."""

from __future__ import annotations

import logging
import tempfile
from unittest.mock import MagicMock

import pandas as pd
import pytest

from aker_data.lake import DataLake


@pytest.fixture
def temp_lake() -> DataLake:
    """Create a temporary data lake for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lake = DataLake(base_path=temp_dir)
        yield lake


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": range(10),
            "name": [f"name_{i}" for i in range(10)],
            "value": [i * 10 for i in range(10)],
            "state": ["CA", "NY", "TX", "FL", "WA"] * 2,
        }
    )


class TestDataLakeBasic:
    """Test basic data lake functionality."""

    def test_init_creates_directory(self, temp_lake: DataLake) -> None:
        """Test that initialization creates the base directory."""
        assert temp_lake.base_path.exists()
        assert temp_lake.base_path.is_dir()

    def test_write_creates_partitioned_structure(
        self, temp_lake: DataLake, sample_df: pd.DataFrame
    ) -> None:
        """Test that write creates proper partitioned structure."""
        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Check that partition directory was created
        partition_path = temp_lake.base_path / "test_dataset" / "as_of=2025-06"
        assert partition_path.exists()

        # Check that parquet files were created
        parquet_files = list(partition_path.glob("**/*.parquet"))
        assert len(parquet_files) > 0

    def test_read_returns_correct_data(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test that read returns the correct data."""
        # Write data
        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Read it back
        read_df = temp_lake.read("test_dataset", "2025-06")

        # Check that data matches (order might differ due to partitioning)
        assert len(read_df) == len(sample_df)
        # The read_df will have an 'as_of' column added during write
        expected_columns = set(sample_df.columns) | {"as_of"}
        assert set(read_df.columns) == expected_columns

    def test_read_with_filters(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test reading with column filters."""
        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Read with filter
        filtered_df = temp_lake.read("test_dataset", "2025-06", filters={"state": "CA"})

        # Should only contain California rows
        assert all(filtered_df["state"] == "CA")
        assert len(filtered_df) == 2  # CA appears twice in sample data

    def test_list_datasets(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test listing available datasets."""
        # Initially empty
        assert temp_lake.list_datasets() == []

        # Write data
        temp_lake.write(sample_df, "dataset1", "2025-06")
        temp_lake.write(sample_df, "dataset2", "2025-07")

        # Should list both datasets
        datasets = temp_lake.list_datasets()
        assert "dataset1" in datasets
        assert "dataset2" in datasets

    def test_list_partitions(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test listing partitions for a dataset."""
        # Write data with different partitions
        temp_lake.write(sample_df, "test_dataset", "2025-06")
        temp_lake.write(sample_df, "test_dataset", "2025-07")

        partitions = temp_lake.list_partitions("test_dataset")
        assert "as_of=2025-06" in partitions
        assert "as_of=2025-07" in partitions

    def test_invalid_as_of_format(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test that invalid as_of format raises error."""
        with pytest.raises(ValueError, match="Invalid as_of format"):
            temp_lake.write(sample_df, "test_dataset", "invalid-format")


class TestSchemaEvolution:
    """Test schema evolution functionality."""

    def test_schema_evolution_allowed(self, temp_lake: DataLake) -> None:
        """Test that adding columns is allowed."""
        # Write initial data
        df1 = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        temp_lake.write(df1, "test_dataset", "2025-06")

        # Write data with additional column
        df2 = pd.DataFrame({"id": [3, 4], "name": ["c", "d"], "value": [10, 20]})
        temp_lake.write(df2, "test_dataset", "2025-07")

        # Should be able to read both partitions
        df1_read = temp_lake.read("test_dataset", "2025-06")
        df2_read = temp_lake.read("test_dataset", "2025-07")

        assert len(df1_read) == 2
        assert len(df2_read) == 2
        assert "value" not in df1_read.columns  # Old partition doesn't have new column
        assert "value" in df2_read.columns  # New partition has new column

    def test_removing_columns_raises_error(self, temp_lake: DataLake) -> None:
        """Test that removing columns raises an error."""
        # Write initial data
        df1 = pd.DataFrame({"id": [1, 2], "name": ["a", "b"], "value": [10, 20]})
        temp_lake.write(df1, "test_dataset", "2025-06")

        # Try to write data with missing column
        df2 = pd.DataFrame({"id": [3, 4], "name": ["c", "d"]})  # Missing "value"
        with pytest.raises(ValueError, match="Schema evolution error: removed fields"):
            temp_lake.write(df2, "test_dataset", "2025-07")


class TestLineageTracking:
    """Test lineage tracking integration."""

    def test_write_logs_lineage(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test that write operations are logged to lineage."""
        # Create mock RunContext
        mock_run_context = MagicMock()
        mock_run_context.log_data_lake_operation = MagicMock()
        temp_lake._run_context = mock_run_context

        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Should have logged the operation
        mock_run_context.log_data_lake_operation.assert_called_once()
        call_args = mock_run_context.log_data_lake_operation.call_args.kwargs
        assert call_args["operation"] == "write"
        assert call_args["dataset"] == "test_dataset"
        assert call_args["metadata"]["as_of"] == "2025-06"
        assert call_args["metadata"]["row_count"] == len(sample_df)
        assert call_args["metadata"]["columns"] == list(sample_df.columns)
        call_args = mock_run_context.log_data_lake_operation.call_args
        assert call_args[1]["operation"] == "write"
        assert call_args[1]["dataset"] == "test_dataset"
        assert call_args[1]["metadata"]["row_count"] == len(sample_df)

    def test_read_logs_lineage(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test that read operations are logged to lineage."""
        # Write data first
        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Create mock RunContext
        mock_run_context = MagicMock()
        mock_run_context.log_data_lake_operation = MagicMock()
        temp_lake._run_context = mock_run_context

        # Read data
        read_df = temp_lake.read("test_dataset", "2025-06")

        # Should have logged the operation
        mock_run_context.log_data_lake_operation.assert_called_once()
        call_args = mock_run_context.log_data_lake_operation.call_args.kwargs
        assert call_args["operation"] == "read"
        assert call_args["dataset"] == "test_dataset"
        assert call_args["metadata"]["as_of"] == "2025-06"
        assert call_args["metadata"]["row_count"] == len(read_df)
        call_args = mock_run_context.log_data_lake_operation.call_args
        assert call_args[1]["operation"] == "read"
        assert call_args[1]["dataset"] == "test_dataset"


class TestPartitioning:
    """Test partitioning functionality."""

    def test_partition_by_columns(self, temp_lake: DataLake) -> None:
        """Test partitioning by additional columns."""
        df = pd.DataFrame(
            {"id": range(4), "state": ["CA", "CA", "NY", "NY"], "value": [1, 2, 3, 4]}
        )

        temp_lake.write(df, "test_dataset", "2025-06", partition_by=["state"])

        # Check that state partitions were created (PyArrow creates nested subdirectories)
        dataset_root = temp_lake.base_path / "test_dataset"
        as_of_path = dataset_root / "as_of=2025-06"
        ca_path = as_of_path / "state=CA"
        ny_path = as_of_path / "state=NY"

        assert dataset_root.exists()
        assert as_of_path.exists()
        assert ca_path.exists() and any(ca_path.glob("*.parquet"))
        assert ny_path.exists() and any(ny_path.glob("*.parquet"))

        # Check data in each partition
        ca_data = temp_lake.read("test_dataset", "2025-06", filters={"state": "CA"})
        ny_data = temp_lake.read("test_dataset", "2025-06", filters={"state": "NY"})

        assert len(ca_data) == 2
        assert len(ny_data) == 2
        assert all(ca_data["state"] == "CA")
        assert all(ny_data["state"] == "NY")


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_write_read_roundtrip(self, temp_lake: DataLake, sample_df: pd.DataFrame) -> None:
        """Test complete write-read roundtrip."""
        # Write data
        temp_lake.write(sample_df, "test_dataset", "2025-06")

        # Read it back
        read_df = temp_lake.read("test_dataset", "2025-06")

        # Basic checks
        assert len(read_df) == len(sample_df)
        # The read_df will have an 'as_of' column added during write
        expected_columns = set(sample_df.columns) | {"as_of"}
        assert set(read_df.columns) == expected_columns

        # Data integrity check (values should match even if order differs)
        assert set(read_df["id"]) == set(sample_df["id"])

    def test_multiple_partitions(self, temp_lake: DataLake) -> None:
        """Test reading from multiple partitions."""
        df1 = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        df2 = pd.DataFrame({"id": [3, 4], "value": [30, 40]})

        temp_lake.write(df1, "test_dataset", "2025-06")
        temp_lake.write(df2, "test_dataset", "2025-07")

        # Read all data
        all_data = temp_lake.read("test_dataset")
        assert len(all_data) == 4

        # Read specific partitions
        june_data = temp_lake.read("test_dataset", "2025-06")
        july_data = temp_lake.read("test_dataset", "2025-07")

        assert len(june_data) == 2
        assert len(july_data) == 2


class TestGeospatialValidation:
    """Test geospatial validation behaviour."""

    def test_write_valid_geodataframe_has_no_warnings(
        self, temp_lake: DataLake, caplog: pytest.LogCaptureFixture
    ) -> None:
        geopandas = pytest.importorskip("geopandas")
        from shapely.geometry import Point

        gdf = geopandas.GeoDataFrame(
            {"id": [1, 2], "value": [10, 20]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )

        caplog.set_level(logging.WARNING)
        temp_lake.write(gdf, "geo_dataset", "2025-06")

        messages = [record.message for record in caplog.records if record.name == "aker_data.lake"]
        assert "geometry_validation_failed" not in messages
        assert "crs_validation_warning" not in messages

    def test_write_invalid_geometry_emits_warning(
        self, temp_lake: DataLake, caplog: pytest.LogCaptureFixture
    ) -> None:
        geopandas = pytest.importorskip("geopandas")
        from shapely.geometry import Polygon

        invalid_polygon = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
        gdf = geopandas.GeoDataFrame(
            {"id": [1], "value": [42]},
            geometry=[invalid_polygon],
            crs="EPSG:4326",
        )

        caplog.set_level(logging.WARNING)
        temp_lake.write(gdf, "geo_dataset_invalid", "2025-07")

        messages = [record.message for record in caplog.records if record.name == "aker_data.lake"]
        assert "geometry_validation_failed" in messages

    def test_write_missing_crs_emits_warning(
        self, temp_lake: DataLake, caplog: pytest.LogCaptureFixture
    ) -> None:
        geopandas = pytest.importorskip("geopandas")
        from shapely.geometry import Point

        gdf = geopandas.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(2, 2)],
            crs=None,
        )

        caplog.set_level(logging.WARNING)
        temp_lake.write(gdf, "geo_dataset_no_crs", "2025-08")

        messages = [record.message for record in caplog.records if record.name == "aker_data.lake"]
        assert "crs_validation_warning" in messages
