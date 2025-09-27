"""Tests for isochrone engine and accessibility analysis."""

from __future__ import annotations

from unittest.mock import MagicMock

import geopandas as gpd
import networkx as nx
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon

from aker_geo.isochrones import (
    AmenityAnalyzer,
    IsochroneEngine,
    OSRMEngine,
    ValhallaEngine,
    compute_isochrones,
    count_amenities_in_isochrones,
)


@pytest.fixture
def sample_network_graph():
    """Create a simple network graph for testing."""
    G = nx.Graph()

    # Add nodes (simplified coordinates)
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

    # Add edges (grid network)
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
def sample_amenities():
    """Create sample amenity points for testing."""
    amenities = [
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
            "geometry": amenities,
        }
    )

    return gpd.GeoDataFrame(df, crs="EPSG:4326")


class TestIsochroneEngine:
    """Test IsochroneEngine functionality."""

    def test_engine_initialization(self):
        """Test isochrone engine initialization."""
        engine = IsochroneEngine()
        assert engine.cache_dir is None
        assert hasattr(engine, "logger")

    def test_speed_calculation(self):
        """Test speed calculation for different modes."""
        engine = IsochroneEngine()

        assert engine._get_speed_for_mode("walk") == 4.8
        assert engine._get_speed_for_mode("bike") == 15.0
        assert engine._get_speed_for_mode("drive") == 30.0
        assert engine._get_speed_for_mode("unknown") == 4.8  # Default to walk

    def test_find_nearest_node(self, sample_network_graph):
        """Test finding nearest node in graph."""
        engine = IsochroneEngine()

        # Test point near node 0
        test_point = Point(0.1, 0.1)
        nearest = engine._find_nearest_node(sample_network_graph, test_point)

        assert nearest is not None
        assert isinstance(nearest, int)

    def test_compute_single_isochrone(self, sample_network_graph):
        """Test single isochrone computation."""
        engine = IsochroneEngine()

        origin_node = 0  # Bottom-left corner
        max_distance_km = 1.0

        isochrone = engine._compute_single_isochrone(
            sample_network_graph, origin_node, max_distance_km, "walk"
        )

        assert isinstance(isochrone, Polygon)
        assert not isochrone.is_empty

    def test_compute_isochrones(self, sample_network_graph):
        """Test computing multiple isochrones."""
        engine = IsochroneEngine()

        origin_points = [Point(0, 0), Point(2, 2)]
        isochrones = engine.compute_isochrones(
            sample_network_graph, origin_points, mode="walk", max_time_minutes=5
        )

        assert isinstance(isochrones, gpd.GeoDataFrame)
        assert len(isochrones) == 2
        assert "isochrone" in isochrones.columns
        assert "mode" in isochrones.columns

    def test_load_graph_from_osm_requires_osmnx(self):
        """Test that OSM graph loading requires osmnx."""
        engine = IsochroneEngine()

        bbox = (-74.1, 40.7, -74.0, 40.8)

        # This should work if osmnx is available
        # If osmnx is not available, it should raise ImportError
        try:
            graph = engine.load_graph_from_osm(bbox)
            assert graph is not None
        except ImportError:
            # Expected if osmnx is not available
            pytest.skip("OSMNX not available for this test")

    def test_create_graph_from_dataframe(self):
        """Test creating graph from DataFrame data."""
        engine = IsochroneEngine()

        # Create sample edge data
        edges_df = pd.DataFrame({"u": [0, 1, 2], "v": [1, 2, 3], "length": [1.0, 1.0, 1.0]})

        graph = engine.create_graph_from_dataframe(edges_df)

        assert isinstance(graph, nx.Graph)
        assert len(graph.nodes) == 4
        assert len(graph.edges) == 3

    def test_optimize_graph_for_routing(self, sample_network_graph):
        """Test graph optimization for routing."""
        engine = IsochroneEngine()

        optimized_graph = engine.optimize_graph_for_routing(sample_network_graph)

        assert isinstance(optimized_graph, nx.Graph)
        # Should have same or fewer nodes/edges after optimization
        assert len(optimized_graph.nodes) <= len(sample_network_graph.nodes)
        assert len(optimized_graph.edges) <= len(sample_network_graph.edges)


class TestAmenityAnalyzer:
    """Test AmenityAnalyzer functionality."""

    def test_analyzer_initialization(self):
        """Test amenity analyzer initialization."""
        analyzer = AmenityAnalyzer()
        assert hasattr(analyzer, "logger")
        assert hasattr(analyzer, "AMENITY_CATEGORIES")

    def test_count_amenities_in_isochrones(self, sample_amenities):
        """Test counting amenities within isochrones."""
        analyzer = AmenityAnalyzer()

        # Create test isochrones
        isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1), Point(2, 2).buffer(1)],
                "origin_point": [Point(0, 0), Point(2, 2)],
            }
        )

        result = analyzer.count_amenities_in_isochrones(isochrones, sample_amenities)

        assert isinstance(result, gpd.GeoDataFrame)
        assert "grocery_count" in result.columns
        assert "pharmacy_count" in result.columns
        assert "total_amenities" in result.columns

    def test_compute_accessibility_scores(self, sample_amenities):
        """Test computing accessibility scores."""
        analyzer = AmenityAnalyzer()

        # Create test isochrones with amenity counts
        isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1)],
                "grocery_count": [2],
                "pharmacy_count": [1],
                "education_count": [1],
                "total_amenities": [4],
            }
        )

        scored = analyzer.compute_amenity_accessibility_scores(isochrones)

        assert "accessibility_score" in scored.columns
        assert scored["accessibility_score"].iloc[0] > 0

    def test_analyze_amenity_coverage(self, sample_amenities):
        """Test amenity coverage analysis."""
        analyzer = AmenityAnalyzer()

        # Create test isochrones with amenity counts
        isochrones = gpd.GeoDataFrame(
            {"total_amenities": [5, 3, 0], "grocery_count": [2, 1, 0], "pharmacy_count": [1, 1, 0]}
        )

        coverage = analyzer.analyze_amenity_coverage(isochrones)

        assert "total_isochrones" in coverage
        assert "isochrones_with_amenities" in coverage
        assert "avg_amenities_per_isochrone" in coverage
        assert coverage["total_isochrones"] == 3
        assert coverage["isochrones_with_amenities"] == 2

    def test_create_amenity_heatmap(self, sample_amenities):
        """Test creating amenity heatmap data."""
        analyzer = AmenityAnalyzer()

        # Create test isochrones with amenity counts
        isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1)],
                "grocery_count": [2],
                "pharmacy_count": [1],
                "total_amenities": [3],
            }
        )

        heatmap = analyzer.create_amenity_heatmap(isochrones)

        assert isinstance(heatmap, gpd.GeoDataFrame)
        assert "category" in heatmap.columns
        assert "count" in heatmap.columns


class TestRoutingEngines:
    """Test routing engine integrations."""

    def test_osrm_engine_initialization(self):
        """Test OSRM engine initialization."""
        engine = OSRMEngine()
        assert engine.base_url == "http://localhost:5000"
        assert engine.profile_mapping["walk"] == "foot"
        assert engine.profile_mapping["bike"] == "bicycle"

    def test_valhalla_engine_initialization(self):
        """Test Valhalla engine initialization."""
        engine = ValhallaEngine()
        assert engine.base_url == "http://localhost:8002"
        assert engine.profile_mapping["walk"] == "pedestrian"
        assert engine.profile_mapping["bike"] == "bicycle"

    def test_routing_engine_manager(self):
        """Test routing engine manager functionality."""
        from aker_geo.isochrones.routing import RoutingEngineManager

        manager = RoutingEngineManager()

        # Should have no engines initially
        assert len(manager.engines) == 0

        # Register an engine
        mock_engine = MagicMock()
        manager.register_engine("test", mock_engine)

        assert "test" in manager.engines
        assert manager.engines["test"] == mock_engine

    def test_compute_isochrone_with_fallback(self):
        """Test isochrone computation with fallback engines."""
        from aker_geo.isochrones.routing import RoutingEngineManager

        manager = RoutingEngineManager()

        # Register a mock engine
        mock_engine = MagicMock()
        mock_engine.is_healthy.return_value = True
        mock_engine.compute_isochrone.return_value = Point(0, 0).buffer(1)
        manager.register_engine("test", mock_engine)

        origin = Point(-74.0, 40.7)
        result = manager.compute_isochrone_with_fallback(origin, 15, "walk", "test")

        assert result is not None
        assert isinstance(result, Polygon)


class TestIntegration:
    """Integration tests for isochrone functionality."""

    def test_compute_isochrones_function(self, sample_network_graph):
        """Test the main compute_isochrones function."""
        origin_points = [Point(0, 0), Point(2, 2)]

        result = compute_isochrones(
            origin_points=origin_points, mode="walk", max_time_minutes=5, graph=sample_network_graph
        )

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2

    def test_count_amenities_in_isochrones_function(self, sample_amenities):
        """Test the main count_amenities_in_isochrones function."""
        # Create test isochrones
        isochrones = gpd.GeoDataFrame(
            {
                "geometry": [Point(0, 0).buffer(1), Point(2, 2).buffer(1)],
                "origin_point": [Point(0, 0), Point(2, 2)],
            }
        )

        result = count_amenities_in_isochrones(isochrones, sample_amenities)

        assert isinstance(result, gpd.GeoDataFrame)
        assert "grocery_count" in result.columns
        assert "total_amenities" in result.columns


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_origin_points(self):
        """Test handling of empty origin points."""
        engine = IsochroneEngine()

        # Create empty graph
        empty_graph = nx.Graph()

        result = engine.compute_isochrones(empty_graph, [], mode="walk", max_time_minutes=15)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 0

    def test_invalid_mode(self):
        """Test handling of invalid transportation mode."""
        engine = IsochroneEngine()

        # Create simple graph
        graph = nx.Graph()
        graph.add_node(0, x=0, y=0)

        result = engine.compute_isochrones(
            graph, [Point(0, 0)], mode="invalid", max_time_minutes=15
        )

        # Should use default mode (walk) and complete
        assert isinstance(result, gpd.GeoDataFrame)

    def test_network_without_coordinates(self):
        """Test handling of network without coordinate data."""
        engine = IsochroneEngine()

        # Create graph without coordinate data
        graph = nx.Graph()
        graph.add_node(0)
        graph.add_edge(0, 1)

        with pytest.raises(ValueError, match="No nodes found"):
            engine._find_nearest_node(graph, Point(0, 0))


class TestPerformance:
    """Test performance characteristics."""

    def test_large_graph_handling(self):
        """Test handling of larger network graphs."""
        engine = IsochroneEngine()

        # Create a larger grid graph
        size = 10
        graph = nx.grid_2d_graph(size, size)

        # Convert to NetworkX graph with coordinates
        G = nx.Graph()
        for i, (x, y) in enumerate(graph.nodes()):
            G.add_node(i, x=x, y=y)

        for u, v in graph.edges():
            u_idx = list(graph.nodes()).index(u)
            v_idx = list(graph.nodes()).index(v)
            G.add_edge(u_idx, v_idx, length=1.0)

        origin_points = [Point(0, 0), Point(size - 1, size - 1)]

        # Should handle larger graphs
        result = engine.compute_isochrones(G, origin_points, mode="walk", max_time_minutes=5)

        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 2


class TestCRSHandling:
    """Test coordinate reference system handling."""

    def test_crs_preservation(self, sample_network_graph):
        """Test that CRS information is preserved."""
        engine = IsochroneEngine()

        origin_points = [Point(0, 0)]
        isochrones = engine.compute_isochrones(
            sample_network_graph, origin_points, mode="walk", max_time_minutes=5
        )

        # Should be in default CRS
        assert isochrones.crs == "EPSG:4326"

    def test_different_coordinate_systems(self):
        """Test handling of different coordinate systems."""
        from aker_geo.crs import validate_crs_compatibility

        # Test compatible CRS
        assert validate_crs_compatibility("EPSG:4326", "EPSG:3857") is True

        # Test incompatible CRS
        assert validate_crs_compatibility("EPSG:4326", "EPSG:999999") is False
