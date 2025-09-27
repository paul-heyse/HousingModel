## ADDED Requirements
### Requirement: DEM-Based Slope Analysis
The system MUST calculate slope percentages for parcels using USGS DEM data for development feasibility assessment.

#### Scenario: Parcel slope calculation
- **WHEN** `terrain.slope_percent(parcels, dem)` is called
- **THEN** calculates slope percentage for each parcel using DEM elevation data
- **AND** identifies parcels with slope >15° as constrained
- **AND** provides slope statistics (mean, max, std dev) per parcel

#### Scenario: Slope constraint classification
- **WHEN** analyzing slope data
- **THEN** classifies parcels by slope severity (flat, moderate, steep, extreme)
- **AND** calculates percentage of constrained area per parcel
- **AND** supports different slope thresholds for various development types

#### Scenario: Slope data validation
- **WHEN** processing DEM data
- **THEN** validates DEM quality and resolution appropriateness
- **AND** handles missing or corrupted elevation data
- **AND** provides confidence scores for slope calculations

### Requirement: Waterway Buffer Analysis
The system MUST create buffer zones around waterways for environmental constraint analysis.

#### Scenario: Waterway buffer creation
- **WHEN** `buffers.waterway(waterways, distance_range=(100, 300))` is called
- **THEN** creates buffer polygons around waterway features
- **AND** supports configurable buffer distances (100–300 ft)
- **AND** handles multiple waterway types (rivers, streams, wetlands)

#### Scenario: Parcel constraint intersection
- **WHEN** analyzing parcel constraints
- **THEN** identifies parcels intersecting waterway buffers
- **AND** calculates percentage of parcel area within buffer zones
- **AND** provides constraint severity classification

#### Scenario: Multi-distance buffer analysis
- **WHEN** analyzing buffer impacts
- **THEN** supports multiple buffer distances for impact assessment
- **AND** provides graduated constraint scoring
- **AND** enables sensitivity analysis for buffer distance selection

### Requirement: Overlay Constraint Analysis
The system MUST analyze overlay restrictions including noise and viewshed constraints.

#### Scenario: Noise overlay analysis
- **WHEN** processing noise constraint data
- **THEN** identifies parcels within noise-restricted zones
- **AND** calculates noise exposure levels per parcel
- **AND** supports multiple noise source types (airports, highways, rail)

#### Scenario: Viewshed constraint analysis
- **WHEN** analyzing viewshed restrictions
- **THEN** identifies parcels with viewshed protection requirements
- **AND** calculates viewshed impact areas
- **AND** supports scenic corridor and protected view analysis

#### Scenario: Combined overlay constraints
- **WHEN** analyzing multiple overlay types
- **THEN** combines noise, viewshed, and other overlay constraints
- **AND** provides unified constraint scoring
- **AND** identifies parcels with multiple constraint types

### Requirement: Terrain Data Integration
The system MUST integrate multiple terrain and constraint data sources.

#### Scenario: USGS DEM integration
- **WHEN** processing elevation data
- **THEN** downloads and processes USGS DEM tiles
- **AND** handles multiple DEM resolutions and formats
- **AND** provides efficient tiling for large areas

#### Scenario: Waterway data integration
- **WHEN** processing hydrological data
- **THEN** integrates NHD (National Hydrography Dataset) data
- **AND** supports state and local waterway datasets
- **AND** handles data quality and completeness issues

#### Scenario: Overlay data integration
- **WHEN** processing constraint overlays
- **THEN** integrates airport noise contours, highway buffers, rail corridors
- **AND** supports municipal zoning overlay data
- **AND** handles data format and projection differences

### Requirement: Constraint Scoring and Classification
The system MUST provide standardized constraint scoring for market analysis.

#### Scenario: Slope constraint scoring
- **WHEN** calculating supply constraints
- **THEN** provides slope-based constraint scores (0–100)
- **AND** weights by slope severity and parcel area
- **AND** supports different scoring methodologies

#### Scenario: Buffer constraint scoring
- **WHEN** analyzing waterway buffers
- **THEN** provides buffer-based constraint scores
- **AND** considers buffer distance and parcel impact
- **AND** supports multi-criteria constraint evaluation

#### Scenario: Overlay constraint scoring
- **WHEN** combining multiple constraint types
- **THEN** provides unified constraint scores
- **AND** supports configurable constraint weighting
- **AND** enables sensitivity analysis for constraint parameters

### Requirement: Data Quality and Validation
The system MUST ensure data quality for terrain and constraint analysis.

#### Scenario: DEM data validation
- **WHEN** processing elevation data
- **THEN** validates DEM resolution and accuracy
- **AND** identifies and handles data gaps or artifacts
- **AND** provides quality metrics for elevation data

#### Scenario: Waterway data validation
- **WHEN** processing hydrological features
- **THEN** validates waterway classification and completeness
- **AND** identifies missing or incorrect waterway data
- **AND** provides data quality assessments

#### Scenario: Overlay data validation
- **WHEN** processing constraint overlays
- **THEN** validates overlay boundaries and classifications
- **AND** identifies data inconsistencies or errors
- **AND** provides validation reports for constraint data

### Requirement: Spatial Analysis and Processing
The system MUST provide efficient spatial analysis for large-scale terrain processing.

#### Scenario: Large-area DEM processing
- **WHEN** processing DEM data for metropolitan areas
- **THEN** handles millions of elevation points efficiently
- **AND** provides memory-efficient processing
- **AND** supports parallel processing across sub-areas

#### Scenario: Vector-raster operations
- **WHEN** performing spatial intersections
- **THEN** efficiently processes parcel-vector to DEM-raster operations
- **AND** handles coordinate system transformations
- **AND** provides accurate spatial intersection results

#### Scenario: Buffer and overlay operations
- **WHEN** creating constraint buffers
- **THEN** efficiently processes large polygon datasets
- **AND** handles complex spatial operations
- **AND** provides performance optimization for repeated operations

### Requirement: Integration with Market Analysis
The system MUST integrate terrain constraints with market supply analysis.

#### Scenario: Constraint data storage
- **WHEN** computing terrain constraints
- **THEN** stores results in market_supply table fields
- **AND** maintains data lineage and update tracking
- **AND** supports efficient querying and aggregation

#### Scenario: Constraint scoring integration
- **WHEN** computing market supply scores
- **THEN** integrates terrain constraints with regulatory and market factors
- **AND** provides weighted constraint scoring
- **AND** supports multi-factor constraint evaluation

#### Scenario: Incremental constraint updates
- **WHEN** updating constraint data
- **THEN** supports incremental processing for changed areas
- **AND** maintains historical constraint trends
- **AND** optimizes for large-scale geographic updates

### Requirement: Performance and Scalability
The system MUST provide performant terrain analysis at scale.

#### Scenario: DEM processing performance
- **WHEN** processing large DEM datasets
- **THEN** provides sub-second processing for typical MSA analysis
- **AND** handles state-scale processing within acceptable timeframes
- **AND** supports parallel processing for performance

#### Scenario: Memory-efficient processing
- **WHEN** analyzing large geographic areas
- **THEN** processes data in chunks to manage memory usage
- **AND** provides streaming processing for very large datasets
- **AND** supports out-of-core processing when needed

#### Scenario: Caching and optimization
- **WHEN** performing repeated terrain analysis
- **THEN** caches intermediate results and processed data
- **AND** optimizes repeated spatial operations
- **AND** provides performance monitoring and optimization
