## ADDED Requirements
### Requirement: Geospatial Validation Alignment
The data lake SHALL interpret geometry and CRS validation results using the new Pandera-backed helper outputs so that valid datasets are not misclassified and warnings remain actionable.

#### Scenario: Valid GeoDataFrame Persists Without False Warnings
- **GIVEN** a GeoDataFrame whose geometries are valid and whose CRS matches UI or storage expectations
- **WHEN** `DataLake.write` persists the dataset with geometry columns
- **THEN** geometry validation SHALL not raise exceptions or emit warnings, and the partition path SHALL be returned

#### Scenario: Invalid Geometry Surfaces Detailed Warning
- **GIVEN** a GeoDataFrame containing an invalid geometry
- **WHEN** `DataLake.write` runs validation
- **THEN** the logger SHALL include the offending index and Shapely `explain_validity` message sourced from `GeometryValidationResult`

#### Scenario: CRS Validation Uses Compatibility Flags
- **GIVEN** a GeoDataFrame whose CRS metadata is missing or mismatched
- **WHEN** `DataLake.write` inspects the `validate_crs` response
- **THEN** the warning SHALL be driven by `has_crs`, `is_storage_crs`, `is_ui_crs`, or `detected_crs` fields rather than relying on a removed `crs_compatible` value

### Requirement: Supply ETL Error Simulation Integrity
The supply ETL test harness SHALL import the HTTP error type it raises so failure branches are exercised and regressions surface during testing.

#### Scenario: Dummy Response Raises HTTPError With Imported Type
- **WHEN** the test client triggers a >=400 status in `DummyResponse.raise_for_status`
- **THEN** a `requests.HTTPError` SHALL be raised without NameError, allowing the failure branch assertion to execute
