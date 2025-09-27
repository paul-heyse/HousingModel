"""Tests for urban metrics and accessibility analysis."""

from __future__ import annotations

import geopandas as gpd
import networkx as nx
import pandas as pd
import pytest
from shapely.geometry import Point

from aker_core.urban import (
    AccessibilityAnalyzer,
    ConnectivityAnalyzer,
    DemographicsAnalyzer,
    UrbanMetrics,
    compute_urban_accessibility,
)


@pytest.fixture
def sample_network_graph():
    """Create a sample street network graph for testing."""
    G = nx.Graph()

    # Add nodes representing intersections
    nodes = [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
        (0, 2),
        (1, 2),
        (2, 2),
        (3, 2),
    ]

    for i, (x, y) in enumerate(nodes):
        G.add_node(i, x=x, y=y)

    # Add edges representing streets
    for i in range(len(nodes)):
        x, y = nodes[i]
        # Connect to right neighbor
        if x < 3:
            G.add_edge(i, i + 1, length=1.0)
        # Connect to bottom neighbor
        if y < 2:
            bottom_idx = i + 4
            G.add_edge(i, bottom_idx, length=1.0)

    return G


@pytest.fixture
def sample_pois():
    """Create sample points of interest for testing."""
    pois = [
        Point(0.5, 0.5),  # Grocery
        Point(1.5, 0.5),  # Pharmacy
        Point(2.5, 0.5),  # School
        Point(0.5, 1.5),  # Transit
        Point(1.5, 1.5),  # Recreation
    ]

    df = pd.DataFrame(
        {
            "amenity": ["supermarket", "pharmacy", "school", "bus_stop", "park"],
            "name": ["Test Grocery", "Test Pharmacy", "Test School", "Test Transit", "Test Park"],
            "geometry": pois,
        }
    )

    return gpd.GeoDataFrame(df, crs="EPSG:4326")


@pytest.fixture
def sample_employment_data():
    """Create sample employment data for testing."""
    employment_points = [
        Point(-74.0059, 40.7128),  # NYC
        Point(-118.2437, 34.0522),  # LA
        Point(-87.6298, 41.8781),  # Chicago
    ]

    df = pd.DataFrame({"employment": [50000, 30000, 25000], "geometry": employment_points})

    return gpd.GeoDataFrame(df, crs="EPSG:4326")


class TestUrbanMetricsModel:
    """Test UrbanMetrics data model."""

    def test_urban_metrics_creation(self):
        """Test creating UrbanMetrics instance."""
        metrics = UrbanMetrics(
            msa_id="12345",
            msa_name="Test MSA",
            state="CA",
            walk_15_grocery_ct=5,
            walk_15_pharmacy_ct=3,
            walk_15_total_ct=15,
            interx_km2=25.5,
            bikeway_conn_idx=75.0,
            retail_vac=8.5,
            retail_rent_qoq=2.1,
            daytime_pop_1mi=45000,
        )

        assert metrics.msa_id == "12345"
        assert metrics.walk_15_grocery_ct == 5
        assert metrics.interx_km2 == 25.5

    def test_composite_score_calculation(self):
        """Test composite score calculation."""
        metrics = UrbanMetrics(
            msa_id="12345",
            msa_name="Test MSA",
            state="CA",
            walk_15_grocery_ct=8,  # 80% of max
            walk_15_pharmacy_ct=6,  # 60% of max
            walk_15_healthcare_ct=7,  # 70% of max
            walk_15_education_ct=9,  # 90% of max
            walk_15_transit_ct=4,  # 40% of max
            interx_km2=30.0,  # 60% of max
            bikeway_conn_idx=80.0,  # 80% of max
            retail_vac=5.0,  # 95% health score
            retail_rent_qoq=1.5,  # Additional 15% bonus
        )

        metrics.calculate_composite_scores()

        # Check that scores are calculated and within bounds
        assert 0 <= metrics.walk_15_score <= 100
        assert 0 <= metrics.bike_15_score <= 100
        assert 0 <= metrics.connectivity_score <= 100
        assert 0 <= metrics.retail_health_score <= 100
        assert 0 <= metrics.urban_convenience_score <= 100

    def test_serialization(self):
        """Test model serialization."""
        metrics = UrbanMetrics(
            msa_id="12345", msa_name="Test MSA", state="CA", walk_15_grocery_ct=5, interx_km2=25.5
        )

        # Test dict conversion
        data_dict = metrics.to_dict()
        assert data_dict["msa_id"] == "12345"
        assert data_dict["walk_15_grocery_ct"] == 5

        # Test JSON conversion
        json_str = metrics.to_json()
        assert isinstance(json_str, str)


class TestAccessibilityAnalyzer:
    """Test AccessibilityAnalyzer functionality."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = AccessibilityAnalyzer()
        assert hasattr(analyzer, "amenity_categories")
        assert "grocery" in analyzer.amenity_categories

    def test_poi_counting(self, sample_pois):
        """Test POI counting within isochrones."""
        analyzer = AccessibilityAnalyzer()

        # Create test isochrones
        isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1), Point(2, 2).buffer(1)],
                "origin_point": [Point(0, 0), Point(2, 2)],
            }
        )

        result = analyzer.count_amenities_in_isochrones(isochrones, sample_pois)

        assert isinstance(result, gpd.GeoDataFrame)
        assert "grocery_count" in result.columns
        assert "total_amenities" in result.columns

    def test_accessibility_scoring(self):
        """Test accessibility score computation."""
        analyzer = AccessibilityAnalyzer()

        # Create test isochrones with amenity counts
        isochrones = gpd.GeoDataFrame(
            {
                "grocery_count": [8, 6],
                "pharmacy_count": [4, 2],
                "education_count": [3, 1],
                "total_amenities": [15, 9],
            }
        )

        scored = analyzer.compute_amenity_accessibility_scores(isochrones)

        assert "accessibility_score" in scored.columns
        assert len(scored) == 2

    def test_coverage_analysis(self):
        """Test amenity coverage analysis."""
        analyzer = AccessibilityAnalyzer()

        # Create test isochrones with amenity counts
        isochrones = gpd.GeoDataFrame(
            {"total_amenities": [10, 5, 0], "grocery_count": [5, 2, 0], "pharmacy_count": [3, 1, 0]}
        )

        coverage = analyzer.analyze_amenity_coverage(isochrones)

        assert "total_isochrones" in coverage
        assert "isochrones_with_amenities" in coverage
        assert coverage["total_isochrones"] == 3
        assert coverage["isochrones_with_amenities"] == 2


class TestConnectivityAnalyzer:
    """Test ConnectivityAnalyzer functionality."""

    def test_intersection_density_calculation(self, sample_network_graph):
        """Test intersection density calculation."""
        analyzer = ConnectivityAnalyzer()

        # Calculate for a 1x1 km area
        density = analyzer.intersection_density(sample_network_graph, 1.0)

        # Should be positive for our test graph
        assert density >= 0

    def test_bikeway_connectivity_calculation(self, sample_network_graph):
        """Test bikeway connectivity calculation."""
        analyzer = ConnectivityAnalyzer()

        connectivity = analyzer.bikeway_connectivity(sample_network_graph)

        # Should be between 0 and 100
        assert 0 <= connectivity <= 100

    def test_street_network_analysis(self, sample_network_graph):
        """Test street network analysis."""
        analyzer = ConnectivityAnalyzer()

        metrics = analyzer.street_network_analysis(sample_network_graph)

        assert "node_count" in metrics
        assert "edge_count" in metrics
        assert "average_degree" in metrics
        assert metrics["node_count"] > 0
        assert metrics["edge_count"] > 0

    def test_walkability_index(self, sample_network_graph, sample_pois):
        """Test walkability index calculation."""
        analyzer = ConnectivityAnalyzer()

        # Test with bounding box
        bbox = (0, 0, 3, 2)  # Approximate bounds of our test graph
        walkability = analyzer.walkability_index(sample_network_graph, sample_pois, bbox)

        assert 0 <= walkability <= 100


class TestDemographicsAnalyzer:
    """Test DemographicsAnalyzer functionality."""

    def test_daytime_population_calculation(self, sample_employment_data):
        """Test daytime population calculation."""
        analyzer = DemographicsAnalyzer()

        # Test with single centroid
        centroid = Point(-74.0059, 40.7128)  # NYC coordinates
        result = analyzer.daytime_population(
            sample_employment_data, buffer_radius_miles=1.0, centroid_points=[centroid]
        )

        assert "total_daytime_population" in result
        assert "avg_daytime_population" in result
        assert "buffer_radius_miles" in result

    def test_employment_density_analysis(self, sample_employment_data):
        """Test employment density analysis."""
        analyzer = DemographicsAnalyzer()

        # Test with bounding box
        bbox = (-74.1, 40.7, -74.0, 40.8)
        result = analyzer.employment_density_analysis(sample_employment_data, bbox)

        assert "total_employment" in result
        assert "area_km2" in result
        assert "employment_density" in result

    def test_population_flow_analysis(self):
        """Test population flow analysis."""
        analyzer = DemographicsAnalyzer()

        # Test data
        origin_data = pd.DataFrame({"flow": [1000, 2000]})
        destination_data = pd.DataFrame({"flow": [1500, 2500]})

        result = analyzer.population_flow_analysis(origin_data, destination_data)

        assert "total_inflow" in result
        assert "total_outflow" in result
        assert "net_flow" in result
        assert result["net_flow"] == 500  # 4000 - 3000


class TestIntegration:
    """Integration tests for urban metrics."""

    def test_compute_urban_accessibility_function(self, sample_network_graph, sample_pois):
        """Test the main compute_urban_accessibility function."""
        origin_points = [Point(0, 0), Point(2, 2)]
        bbox = (0, 0, 3, 2)

        result = compute_urban_accessibility(
            origin_points=origin_points, amenities_gdf=sample_pois, bbox=bbox
        )

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2
        # Should have accessibility columns
        assert any(col.startswith("walk_15_") for col in result.columns)

    def test_end_to_end_urban_analysis(
        self, sample_network_graph, sample_pois, sample_employment_data
    ):
        """Test end-to-end urban analysis workflow."""
        # 1. Compute isochrones
        origin_points = [Point(0, 0)]
        bbox = (0, 0, 3, 2)

        from aker_geo.isochrones import compute_isochrones

        isochrones = compute_isochrones(
            origin_points=origin_points,
            mode="walk",
            max_time_minutes=15,
            bbox=bbox,
            graph=sample_network_graph,
        )

        # 2. Count amenities
        from aker_geo.isochrones import count_amenities_in_isochrones

        accessibility = count_amenities_in_isochrones(isochrones, sample_pois)

        # 3. Calculate connectivity
        from aker_core.urban import ConnectivityAnalyzer

        analyzer = ConnectivityAnalyzer()
        connectivity = analyzer.walkability_index(sample_network_graph, sample_pois, bbox)

        # 4. Calculate demographics
        from aker_core.urban import DemographicsAnalyzer

        demo_analyzer = DemographicsAnalyzer()
        demographics = demo_analyzer.daytime_population(
            sample_employment_data, centroid_points=[Point(0, 0)]
        )

        # Verify all components work together
        assert isinstance(isochrones, gpd.GeoDataFrame)
        assert isinstance(accessibility, gpd.GeoDataFrame)
        assert isinstance(connectivity, float)
        assert isinstance(demographics, dict)

    def test_urban_metrics_model_integration(self):
        """Test UrbanMetrics model integration."""
        metrics = UrbanMetrics(
            msa_id="12345",
            msa_name="Test MSA",
            state="CA",
            walk_15_grocery_ct=5,
            walk_15_pharmacy_ct=3,
            walk_15_total_ct=12,
            interx_km2=25.5,
            bikeway_conn_idx=75.0,
            retail_vac=8.5,
            retail_rent_qoq=2.1,
            daytime_pop_1mi=45000,
        )

        metrics.calculate_composite_scores()

        # Verify all scores are calculated and within bounds
        assert 0 <= metrics.walk_15_score <= 100
        assert 0 <= metrics.bike_15_score <= 100
        assert 0 <= metrics.connectivity_score <= 100
        assert 0 <= metrics.retail_health_score <= 100
        assert 0 <= metrics.urban_convenience_score <= 100


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_amenities(self):
        """Test handling of empty amenities data."""
        analyzer = AccessibilityAnalyzer()

        # Create empty isochrones
        isochrones = gpd.GeoDataFrame(columns=["geometry"])
        empty_pois = gpd.GeoDataFrame(columns=["amenity", "geometry"])

        result = analyzer.count_amenities_in_isochrones(isochrones, empty_pois)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 0

    def test_invalid_geometry_handling(self):
        """Test handling of invalid geometries."""
        analyzer = AccessibilityAnalyzer()

        # Create isochrones with invalid geometry
        invalid_isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1), None],  # One valid, one None
                "origin_point": [Point(0, 0), Point(1, 1)],
            }
        )

        pois = gpd.GeoDataFrame({"amenity": ["test"], "geometry": [Point(0.5, 0.5)]})

        result = analyzer.count_amenities_in_isochrones(invalid_isochrones, pois)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2

    def test_network_without_coordinates(self):
        """Test handling of network without coordinate data."""
        analyzer = ConnectivityAnalyzer()

        # Create graph without coordinate data
        graph = nx.Graph()
        graph.add_node(0)
        graph.add_edge(0, 1)

        with pytest.raises(ValueError):
            analyzer.intersection_density(graph, 1.0)


class TestPerformance:
    """Test performance characteristics."""

    def test_large_network_handling(self):
        """Test handling of larger network graphs."""
        analyzer = ConnectivityAnalyzer()

        # Create a larger grid graph
        size = 20
        graph = nx.grid_2d_graph(size, size)

        # Convert to NetworkX graph with coordinates
        G = nx.Graph()
        for i, (x, y) in enumerate(graph.nodes()):
            G.add_node(i, x=x, y=y)

        for u, v in graph.edges():
            u_idx = list(graph.nodes()).index(u)
            v_idx = list(graph.nodes()).index(v)
            G.add_edge(u_idx, v_idx, length=1.0)

        # Should handle larger graphs
        metrics = analyzer.street_network_analysis(G)
        assert metrics["node_count"] == size * size
        assert metrics["edge_count"] > 0


class TestDataIntegration:
    """Test integration with other data systems."""

    def test_urban_metrics_with_real_data_structure(self):
        """Test urban metrics with realistic data structure."""
        # Create realistic urban metrics
        metrics = UrbanMetrics(
            msa_id="35620",
            msa_name="New York-Newark-Jersey City, NY-NJ-PA",
            state="NY",
            walk_15_grocery_ct=45,
            walk_15_pharmacy_ct=28,
            walk_15_healthcare_ct=32,
            walk_15_education_ct=38,
            walk_15_transit_ct=156,
            walk_15_recreation_ct=23,
            walk_15_shopping_ct=89,
            walk_15_dining_ct=234,
            walk_15_banking_ct=67,
            walk_15_services_ct=45,
            walk_15_total_ct=757,
            interx_km2=89.5,
            bikeway_conn_idx=78.3,
            retail_vac=6.2,
            retail_rent_qoq=1.8,
            daytime_pop_1mi=125000,
        )

        metrics.calculate_composite_scores()

        # Verify realistic scores
        assert metrics.walk_15_score > 50  # Should be high for NYC
        assert metrics.urban_convenience_score > 60  # Should be high for NYC
        assert 0 <= metrics.urban_convenience_score <= 100
