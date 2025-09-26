"""Parquet data lake with Hive-style partitioning and schema evolution support."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from great_expectations.core.batch import BatchRequest
from great_expectations.core.expectation_validation_result import ExpectationSuiteValidationResult
from great_expectations.data_context import FileDataContext


class DataLake:
    """Parquet data lake with Hive-style partitioning."""

    def __init__(
        self, base_path: Union[str, Path] = "/lake", run_context: Optional[Any] = None
    ) -> None:
        """Initialize data lake with base path.

        Args:
            base_path: Base directory for the data lake (default: /lake)
            run_context: Optional RunContext for lineage tracking
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._run_context = run_context

    def write(
        self,
        df: pd.DataFrame,
        dataset: str,
        as_of: str,
        partition_by: Optional[List[str]] = None,
        ge_context: Optional[FileDataContext] = None,
        ge_suite: Optional[str] = None,
    ) -> str:
        """Write DataFrame to partitioned Parquet format.

        Args:
            df: DataFrame to write
            dataset: Dataset name (e.g., 'acs_income')
            as_of: Time partition (YYYY-MM format, e.g., '2025-06')
            partition_by: Additional columns to partition by
            ge_context: Great Expectations context for validation
            ge_suite: Expectation suite name for validation

        Returns:
            Path to the written dataset partition
        """
        # Validate as_of format
        if not self._validate_as_of(as_of):
            raise ValueError(f"Invalid as_of format: {as_of}. Expected YYYY-MM")

        # Create dataset directory
        dataset_path = self.base_path / dataset
        dataset_path.mkdir(exist_ok=True)

        # Validate schema evolution if dataset exists
        existing_schema = self._get_latest_schema(dataset)
        if existing_schema is not None:
            self._validate_schema_evolution(df, existing_schema)

        # Run Great Expectations validation if configured
        if ge_context and ge_suite:
            self._run_ge_validation(df, ge_context, ge_suite)

        # Validate geospatial data if geometry columns exist
        if self._has_geometry_columns(df):
            try:
                from aker_core.validation import validate_geometry, validate_crs

                # Validate geometry integrity
                geom_validation = validate_geometry(df)
                if not geom_validation.success:
                    self.logger.warning(f"Geometry validation failed for {dataset}: {geom_validation.failed_expectations}")

                # Validate CRS
                crs_validation = validate_crs(df)
                if not crs_validation["crs_compatible"]:
                    self.logger.warning(f"CRS compatibility issues for {dataset}: {crs_validation}")

            except ImportError:
                # Geospatial libraries not available, skip validation
                pass
            except Exception as e:
                self.logger.warning(f"Geospatial validation failed for {dataset}: {e}")

        # Write to Parquet with partitioning
        partition_cols = ["as_of"] + (partition_by or [])

        # Add as_of column if not present
        df_with_as_of = df.copy()
        if "as_of" not in df_with_as_of.columns:
            df_with_as_of["as_of"] = as_of

        # Handle geometry columns for Parquet storage
        df_for_parquet = df_with_as_of.copy()
        if self._has_geometry_columns(df_with_as_of):
            # Convert geometry columns to WKT for Parquet storage
            import geopandas as gpd
            if isinstance(df_with_as_of, gpd.GeoDataFrame):
                for geom_col in df_with_as_of.columns:
                    if df_with_as_of[geom_col].dtype == 'geometry':
                        df_for_parquet[geom_col] = df_with_as_of[geom_col].astype(str)

        # Write partitioned parquet
        partition_path = dataset_path / f"as_of={as_of}"
        table = pa.Table.from_pandas(df_for_parquet)

        if partition_cols:
            pq.write_to_dataset(
                table,
                root_path=str(dataset_path),
                partition_cols=partition_cols,
                filesystem=pa.fs.LocalFileSystem(),
                compression="snappy",
            )
        else:
            partition_path.mkdir(parents=True, exist_ok=True)
            pq.write_table(
                table,
                str(partition_path / "data.parquet"),
                compression="snappy",
            )

        partition_path = dataset_path / f"as_of={as_of}"
        # Log operation to lineage if RunContext is available
        if self._run_context and hasattr(self._run_context, "log_data_lake_operation"):
            self._run_context.log_data_lake_operation(
                operation="write",
                dataset=dataset,
                path=str(partition_path),
                metadata={
                    "as_of": as_of,
                    "partition_by": partition_by,
                    "row_count": len(df),
                    "columns": list(df.columns),
                },
            )

        return str(partition_path)

    def read(
        self,
        dataset: str,
        as_of: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Read DataFrame from partitioned Parquet format.

        Args:
            dataset: Dataset name
            as_of: Specific time partition to read (optional)
            filters: Additional column filters

        Returns:
            DataFrame with requested data
        """
        dataset_path = self.base_path / dataset

        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset '{dataset}' not found in data lake")

        # Use DuckDB for efficient partition-aware reading
        con = duckdb.connect()

        # Build query with partition filtering
        query_parts = []
        if as_of:
            query_parts.append(f"as_of = '{as_of}'")

        if filters:
            for col, value in filters.items():
                if isinstance(value, str):
                    query_parts.append(f"{col} = '{value}'")
                else:
                    query_parts.append(f"{col} = {value}")

        where_clause = " AND ".join(query_parts) if query_parts else "1=1"

        # Use glob pattern for efficient partition reading
        if as_of:
            pattern = f"{dataset_path}/as_of={as_of}/**/*.parquet"
        else:
            pattern = f"{dataset_path}/**/*.parquet"

        try:
            # DuckDB query with predicate pushdown
            query = f"""
                SELECT * FROM read_parquet('{pattern}')
                WHERE {where_clause}
            """
            df = con.execute(query).fetchdf()

            # Convert WKT geometry columns back to geometry objects if needed
            df = self._convert_wkt_to_geometry(df)

            # Validate geospatial data if geometry columns exist
            if self._has_geometry_columns(df):
                try:
                    from aker_core.validation import validate_geometry, validate_crs

                    # Validate geometry integrity
                    geom_validation = validate_geometry(df)
                    if not geom_validation.success:
                        self.logger.warning(f"Geometry validation failed for {dataset}: {geom_validation.failed_expectations}")

                    # Validate CRS
                    crs_validation = validate_crs(df)
                    if not crs_validation["crs_compatible"]:
                        self.logger.warning(f"CRS compatibility issues for {dataset}: {crs_validation}")

                except ImportError:
                    # Geospatial libraries not available, skip validation
                    pass
                except Exception as e:
                    self.logger.warning(f"Geospatial validation failed for {dataset}: {e}")

            # Log operation to lineage if RunContext is available
            if self._run_context and hasattr(self._run_context, "log_data_lake_operation"):
                self._run_context.log_data_lake_operation(
                    operation="read",
                    dataset=dataset,
                    path=pattern,
                    metadata={
                        "as_of": as_of,
                        "filters": filters,
                        "row_count": len(df),
                        "columns": list(df.columns),
                    },
                )

            return df
        except Exception as e:
            raise RuntimeError(f"Failed to read dataset '{dataset}': {e}")

    def list_datasets(self) -> List[str]:
        """List all available datasets in the data lake."""
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]

    def list_partitions(self, dataset: str) -> List[str]:
        """List all partitions for a dataset."""
        dataset_path = self.base_path / dataset
        if not dataset_path.exists():
            return []

        partitions = set()
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.endswith(".parquet"):
                    # Extract partition info from path
                    rel_path = os.path.relpath(root, dataset_path)
                    if "=" in rel_path:
                        # Get just the partition part (e.g., "as_of=2025-06" from "as_of=2025-06/as_of=2025-06")
                        parts = rel_path.split("/")
                        for part in parts:
                            if "=" in part:
                                partitions.add(part)

        return sorted(list(partitions))

    def _has_geometry_columns(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has geometry columns."""
        try:
            import geopandas as gpd
            return isinstance(df, gpd.GeoDataFrame) or 'geometry' in df.columns
        except ImportError:
            return 'geometry' in df.columns

    def _convert_wkt_to_geometry(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert WKT geometry columns back to geometry objects."""
        try:
            import geopandas as gpd
            from shapely import wkt

            # Check if we have any string columns that might contain WKT
            df_result = df.copy()

            # Look for columns that might contain geometry data as strings
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Check if the first non-null value looks like WKT
                    sample_values = df[col].dropna().head(5)
                    if len(sample_values) > 0:
                        sample = str(sample_values.iloc[0])
                        if sample.startswith(('POINT', 'POLYGON', 'LINESTRING', 'MULTI')):
                            try:
                                # Try to parse as WKT
                                df_result[col] = df[col].apply(lambda x: wkt.loads(str(x)) if pd.notna(x) else None)
                                # Convert to GeoDataFrame if we have a geometry column
                                if col == 'geometry' and not isinstance(df_result, gpd.GeoDataFrame):
                                    df_result = gpd.GeoDataFrame(df_result)
                            except Exception:
                                # Not valid WKT, skip
                                pass

            return df_result
        except ImportError:
            # Geospatial libraries not available
            return df

    def _validate_as_of(self, as_of: str) -> bool:
        """Validate as_of format (YYYY-MM)."""
        try:
            year, month = as_of.split("-")
            return len(year) == 4 and len(month) == 2 and year.isdigit() and month.isdigit()
        except ValueError:
            return False

    def _get_latest_schema(self, dataset: str) -> Optional[pa.Schema]:
        """Get the schema from the most recent partition."""
        partitions = self.list_partitions(dataset)
        if not partitions:
            return None

        # Get the latest partition
        latest_partition = max(partitions)

        try:
            # Read schema from the latest partition
            partition_path = self.base_path / dataset / latest_partition
            parquet_file = next(partition_path.glob("**/*.parquet"))
            return pq.read_schema(parquet_file)
        except (StopIteration, Exception):
            return None

    def _validate_schema_evolution(self, df: pd.DataFrame, existing_schema: pa.Schema) -> None:
        """Validate that new data is compatible with existing schema."""
        new_schema = pa.Table.from_pandas(df).schema

        # Check for breaking changes (removed columns)
        existing_fields = {field.name for field in existing_schema}
        new_fields = {field.name for field in new_schema}

        removed_fields = existing_fields - new_fields
        if removed_fields:
            raise ValueError(f"Schema evolution error: removed fields {removed_fields}")

        # Schema evolution is allowed (new columns, type changes within compatibility)

    def _run_ge_validation(
        self, df: pd.DataFrame, context: FileDataContext, suite_name: str
    ) -> ExpectationSuiteValidationResult:
        """Run Great Expectations validation suite."""
        # Create a temporary batch for validation
        batch_request = BatchRequest(
            datasource_name="pandas",
            data_connector_name="runtime",
            data_asset_name="temp_validation",
            runtime_parameters={"batch_data": df},
            batch_spec_passthrough={"reader_method": "read_csv"},
        )

        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=suite_name,
        )

        results = validator.validate()
        return results
