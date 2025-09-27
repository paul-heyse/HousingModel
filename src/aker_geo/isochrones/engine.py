"""Core isochrone computation engine using networkx and osmnx."""

from __future__ import annotations

import logging
from typing import List, Optional, Union

import geopandas as gpd
import networkx as nx
import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

try:
    import osmnx as ox

    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False

# Simplified logging for now
logger = logging.getLogger(__name__)


class IsochroneEngine:
    """Engine for computing isochrones using street network graphs."""

    # Speed assumptions in km/h
    WALK_SPEED_KMH = 4.8  # Typical walking speed
    BIKE_SPEED_KMH = 15.0  # Typical biking speed

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize isochrone engine.

        Args:
            cache_dir: Directory for caching network graphs
        """
        self.cache_dir = cache_dir
        self.logger = logger
        self.graph_cache = {}

        if not HAS_OSMNX:
            self.logger.warning("OSMNX not available, using networkx fallback")

    def compute_isochrones(
        self,
        graph: nx.Graph,
        origin_points: Union[List[Point], gpd.GeoSeries, pd.Series],
        mode: str = "walk",
        max_time_minutes: int = 15,
        network_type: str = "walk",
    ) -> gpd.GeoDataFrame:
        """Compute isochrones from origin points using network graph.

        Args:
            graph: NetworkX graph representing street network
            origin_points: List of Point geometries or coordinate tuples
            mode: Transportation mode ("walk", "bike", "drive")
            max_time_minutes: Maximum travel time in minutes
            network_type: OSM network type ("walk", "bike", "drive", "all")

        Returns:
            GeoDataFrame with isochrone polygons for each origin point
        """
        self.logger.info(
            f"Computing isochrones for {len(origin_points)} points, mode={mode}, max_time={max_time_minutes}min"
        )

        # Normalize origin points
        if isinstance(origin_points, (list, pd.Series)):
            if len(origin_points) == 0:
                return gpd.GeoDataFrame()  # Return empty GeoDataFrame
            if isinstance(origin_points[0], (tuple, list)):
                # Convert coordinate tuples to Points
                origin_points = [Point(x, y) for x, y in origin_points]
            origin_points = gpd.GeoSeries(origin_points)

        # Get speed for mode
        speed_kmh = self._get_speed_for_mode(mode)

        # Convert time to distance (km)
        max_distance_km = (speed_kmh * max_time_minutes) / 60

        self.logger.info(f"Max distance: {max_distance_km:.2f} km")

        # Compute isochrones for each origin point
        isochrone_polygons = []

        for i, origin_point in enumerate(origin_points):
            try:
                # Find nearest node in graph
                nearest_node = self._find_nearest_node(graph, origin_point)

                # Compute isochrone using ego graph
                isochrone_polygons.append(
                    {
                        "origin_point": origin_point,
                        "isochrone": self._compute_single_isochrone(
                            graph, nearest_node, max_distance_km, network_type
                        ),
                        "mode": mode,
                        "max_time_minutes": max_time_minutes,
                        "max_distance_km": max_distance_km,
                    }
                )

            except Exception as e:
                self.logger.error(f"Failed to compute isochrone for point {i}: {e}")
                # Add empty polygon for failed computation
                isochrone_polygons.append(
                    {
                        "origin_point": origin_point,
                        "isochrone": Polygon(),
                        "mode": mode,
                        "max_time_minutes": max_time_minutes,
                        "max_distance_km": max_distance_km,
                        "error": str(e),
                    }
                )

        # Create GeoDataFrame
        result_gdf = gpd.GeoDataFrame(isochrone_polygons)
        result_gdf = result_gdf.set_geometry("isochrone")

        # Set CRS to match the input graph
        if hasattr(graph, "graph") and "crs" in graph.graph:
            result_gdf.crs = graph.graph["crs"]
        else:
            # Default to WGS84
            result_gdf.crs = "EPSG:4326"

        self.logger.info(f"Computed {len(isochrone_polygons)} isochrones")
        return result_gdf

    def _get_speed_for_mode(self, mode: str) -> float:
        """Get speed in km/h for transportation mode."""
        speeds = {
            "walk": self.WALK_SPEED_KMH,
            "bike": self.BIKE_SPEED_KMH,
            "drive": 30.0,  # Typical driving speed in urban areas
        }
        return speeds.get(mode.lower(), self.WALK_SPEED_KMH)

    def _find_nearest_node(self, graph: nx.Graph, point: Point) -> int:
        """Find the nearest node in the graph to a point."""
        # For now, use a simple approach - in practice you'd use spatial indexing
        # This is a simplified implementation
        min_distance = float("inf")
        nearest_node = None

        for node in graph.nodes():
            if "x" in graph.nodes[node] and "y" in graph.nodes[node]:
                node_point = Point(graph.nodes[node]["x"], graph.nodes[node]["y"])
                distance = point.distance(node_point)
                if distance < min_distance:
                    min_distance = distance
                    nearest_node = node

        if nearest_node is None:
            raise ValueError("No nodes found in graph")

        return nearest_node

    def _compute_single_isochrone(
        self, graph: nx.Graph, origin_node: int, max_distance_km: float, network_type: str
    ) -> Polygon:
        """Compute isochrone polygon for a single origin node."""
        # Use ego graph approach - find all nodes within distance
        # This is a simplified implementation
        subgraph = nx.ego_graph(
            graph, origin_node, radius=max_distance_km * 1000
        )  # Convert to meters

        # Extract boundary nodes
        boundary_nodes = []
        for node in subgraph.nodes():
            # Calculate distance from origin
            if "x" in graph.nodes[node] and "y" in graph.nodes[node]:
                node_point = Point(graph.nodes[node]["x"], graph.nodes[node]["y"])
                origin_point = Point(graph.nodes[origin_node]["x"], graph.nodes[origin_node]["y"])
                distance = origin_point.distance(node_point)

                if distance <= max_distance_km * 1000:  # Convert back to meters
                    boundary_nodes.append(node_point)

        if not boundary_nodes:
            return Polygon()

        # Create convex hull of boundary points
        try:
            boundary_geom = unary_union(boundary_nodes)
            if boundary_geom.geom_type == "MultiPoint":
                return boundary_geom.convex_hull
            elif boundary_geom.geom_type == "Point":
                # Create small buffer around single point
                return boundary_geom.buffer(max_distance_km * 1000)
            else:
                return boundary_geom
        except Exception:
            return Polygon()

    def load_graph_from_osm(
        self, bbox: tuple[float, float, float, float], network_type: str = "walk"
    ) -> nx.Graph:
        """Load street network graph from OSM data."""
        if not HAS_OSMNX:
            raise ImportError("OSMNX not available for OSM data loading")

        try:
            # Load graph using osmnx
            graph = ox.graph_from_bbox(
                bbox=bbox,  # (west, south, east, north)
                network_type=network_type,
                simplify=True,
                retain_all=False,
            )

            self.logger.info(
                f"Loaded OSM graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges"
            )
            return graph

        except Exception as e:
            self.logger.error(f"Failed to load OSM graph: {e}")
            raise

    def create_graph_from_dataframe(
        self, edges_df: pd.DataFrame, nodes_df: Optional[pd.DataFrame] = None
    ) -> nx.Graph:
        """Create NetworkX graph from DataFrame data."""
        graph = nx.Graph()

        # Add nodes if provided
        if nodes_df is not None:
            for _, node in nodes_df.iterrows():
                graph.add_node(
                    node["node_id"],
                    x=node.get("x", 0),
                    y=node.get("y", 0),
                    **{k: v for k, v in node.items() if k not in ["node_id", "x", "y"]},
                )

        # Add edges
        for _, edge in edges_df.iterrows():
            graph.add_edge(
                edge["u"],
                edge["v"],
                length=edge.get("length", 1),
                **{k: v for k, v in edge.items() if k not in ["u", "v", "length"]},
            )

        self.logger.info(
            f"Created graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges"
        )
        return graph

    def optimize_graph_for_routing(self, graph: nx.Graph) -> nx.Graph:
        """Optimize graph for efficient routing computations."""
        # Remove isolated nodes
        isolated_nodes = list(nx.isolates(graph))
        graph.remove_nodes_from(isolated_nodes)

        # Remove self-loops
        self_loops = list(nx.selfloop_edges(graph))
        graph.remove_edges_from(self_loops)

        self.logger.info(
            f"Optimized graph: removed {len(isolated_nodes)} isolated nodes and {len(self_loops)} self-loops"
        )
        return graph


def compute_isochrones(
    origin_points: Union[List[Point], gpd.GeoSeries, pd.Series],
    mode: str = "walk",
    max_time_minutes: int = 15,
    bbox: Optional[tuple[float, float, float, float]] = None,
    graph: Optional[nx.Graph] = None,
    network_type: str = "walk",
) -> gpd.GeoDataFrame:
    """Compute isochrones from origin points.

    Args:
        origin_points: List of Point geometries or coordinate tuples
        mode: Transportation mode ("walk", "bike", "drive")
        max_time_minutes: Maximum travel time in minutes
        bbox: Bounding box for OSM data (if graph not provided)
        graph: Pre-loaded NetworkX graph (if available)
        network_type: OSM network type for graph loading

    Returns:
        GeoDataFrame with isochrone polygons
    """
    engine = IsochroneEngine()

    # Load or use provided graph
    if graph is None:
        if bbox is None:
            raise ValueError("Either graph or bbox must be provided")
        graph = engine.load_graph_from_osm(bbox, network_type)
        graph = engine.optimize_graph_for_routing(graph)

    return engine.compute_isochrones(graph, origin_points, mode, max_time_minutes, network_type)
