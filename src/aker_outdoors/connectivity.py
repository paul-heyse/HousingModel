"""Urban connectivity analysis for intersection density and bikeway networks."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

from aker_core.logging import get_logger

from ..isochrones import compute_isochrones
from .models import NoiseLevel


class ConnectivityAnalyzer:
    """Analyzer for urban connectivity and walkability metrics."""

    def __init__(self):
        """Initialize connectivity analyzer."""
        self.logger = get_logger(__name__)

    def intersection_density(
        self,
        graph: nx.Graph,
        area_km2: float
    ) -> float:
        """Calculate intersection density per square kilometer.

        Args:
            graph: NetworkX graph representing street network
            area_km2: Area in square kilometers

        Returns:
            Intersection density (intersections per km²)
        """
        if area_km2 <= 0:
            raise ValueError("Area must be positive")

        # Count intersections (nodes with degree > 2)
        intersections = sum(1 for node, degree in graph.degree() if degree > 2)

        density = intersections / area_km2

        self.logger.info(f"Intersection density: {density".2f"} intersections/km²")
        return density

    def bikeway_connectivity(
        self,
        graph: nx.Graph,
        bike_infrastructure: Optional[gpd.GeoDataFrame] = None
    ) -> float:
        """Calculate bikeway connectivity index.

        Args:
            graph: NetworkX graph representing street network
            bike_infrastructure: Optional GeoDataFrame with bike lane data

        Returns:
            Bikeway connectivity index (0-100)
        """
        try:
            # Calculate basic network connectivity
            # This is a simplified implementation - in practice you'd analyze
            # bike lane connectivity, network redundancy, etc.

            # Count bike-friendly edges (simplified heuristic)
            total_edges = len(graph.edges())
            bike_friendly_edges = 0

            for u, v, data in graph.edges(data=True):
                # Simple heuristic: edges with 'highway'='cycleway' or 'bicycle'='yes'
                if (data.get('highway') == 'cycleway' or
                    data.get('bicycle') == 'yes' or
                    data.get('cycleway') in ['lane', 'track', 'shared']):
                    bike_friendly_edges += 1

            # Calculate connectivity ratio
            if total_edges > 0:
                connectivity_ratio = bike_friendly_edges / total_edges
            else:
                connectivity_ratio = 0

            # Convert to 0-100 scale
            connectivity_index = min(connectivity_ratio * 100, 100)

            self.logger.info(f"Bikeway connectivity index: {connectivity_index".1f"}")
            return connectivity_index

        except Exception as e:
            self.logger.error(f"Bikeway connectivity calculation failed: {e}")
            return 0.0

    def street_network_analysis(
        self,
        graph: nx.Graph,
        area_bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict[str, float]:
        """Analyze street network characteristics.

        Args:
            graph: NetworkX graph representing street network
            area_bounds: Optional bounding box (min_lon, min_lat, max_lon, max_lat)

        Returns:
            Dictionary with network analysis metrics
        """
        try:
            metrics = {
                "node_count": len(graph.nodes()),
                "edge_count": len(graph.edges()),
                "average_degree": np.mean([degree for _, degree in graph.degree()]),
                "network_density": nx.density(graph),
                "average_clustering": nx.average_clustering(graph) if len(graph.nodes()) > 0 else 0,
            }

            # Calculate area if bounds provided
            if area_bounds:
                min_lon, min_lat, max_lon, max_lat = area_bounds
                # Approximate area calculation (simplified)
                area_km2 = (max_lon - min_lon) * 111 * (max_lat - min_lat) * 111  # Rough km²
                metrics["intersection_density"] = self.intersection_density(graph, area_km2)

            self.logger.info(f"Network analysis: {metrics['node_count']} nodes, {metrics['edge_count']} edges")
            return metrics

        except Exception as e:
            self.logger.error(f"Street network analysis failed: {e}")
            return {}

    def walkability_index(
        self,
        graph: nx.Graph,
        pois: gpd.GeoDataFrame,
        area_bounds: Tuple[float, float, float, float]
    ) -> float:
        """Calculate walkability index based on connectivity and amenity access.

        Args:
            graph: Street network graph
            pois: Points of interest
            area_bounds: Bounding box for area calculation

        Returns:
            Walkability index (0-100)
        """
        try:
            # Calculate intersection density
            min_lon, min_lat, max_lon, max_lat = area_bounds
            area_km2 = (max_lon - min_lon) * 111 * (max_lat - min_lat) * 111
            intersection_density = self.intersection_density(graph, area_km2)

            # Calculate amenity density
            amenity_count = len(pois)
            amenity_density = amenity_count / area_km2

            # Calculate connectivity score
            connectivity_score = self.bikeway_connectivity(graph)

            # Combine metrics (weighted average)
            walkability = (
                min(intersection_density / 100, 1.0) * 0.4 +  # Intersection density component
                min(amenity_density / 10, 1.0) * 0.4 +      # Amenity density component
                connectivity_score / 100 * 0.2               # Connectivity component
            ) * 100

            self.logger.info(f"Walkability index: {walkability".1f"}")
            return walkability

        except Exception as e:
            self.logger.error(f"Walkability index calculation failed: {e}")
            return 0.0


def intersection_density(graph: nx.Graph, area_km2: float) -> float:
    """Calculate intersection density per square kilometer.

    Args:
        graph: NetworkX graph representing street network
        area_km2: Area in square kilometers

    Returns:
        Intersection density (intersections per km²)
    """
    analyzer = ConnectivityAnalyzer()
    return analyzer.intersection_density(graph, area_km2)


def bikeway_connectivity(
    graph: nx.Graph,
    bike_infrastructure: Optional[gpd.GeoDataFrame] = None
) -> float:
    """Calculate bikeway connectivity index.

    Args:
        graph: NetworkX graph representing street network
        bike_infrastructure: Optional GeoDataFrame with bike lane data

    Returns:
        Bikeway connectivity index (0-100)
    """
    analyzer = ConnectivityAnalyzer()
    return analyzer.bikeway_connectivity(graph, bike_infrastructure)
