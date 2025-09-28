"""Outdoor recreation accessibility analysis for trails, parks, and water access."""

from __future__ import annotations

from typing import List, Optional, Tuple

import geopandas as gpd
from shapely.geometry import Point

from aker_core.logging import get_logger


class RecreationAnalyzer:
    """Analyzer for outdoor recreation accessibility and amenity analysis."""

    def __init__(self):
        """Initialize recreation analyzer."""
        self.logger = get_logger(__name__)

        # Recreation amenity categories for analysis
        self.recreation_categories = {
            "trails": ["trail", "path", "footway", "cycleway"],
            "parks": ["park", "garden", "playground", "recreation_ground"],
            "water": ["lake", "river", "reservoir", "water", "beach"],
            "winter": ["ski", "snowboard", "winter_sports", "ice_rink"],
            "nature": ["forest", "wood", "nature_reserve", "wildlife"]
        }

    def trail_accessibility(
        self,
        origin_points: List[tuple[float, float]],
        trail_network: gpd.GeoDataFrame,
        max_distance_km: float = 5.0
    ) -> gpd.GeoDataFrame:
        """Calculate trail accessibility from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            trail_network: GeoDataFrame with trail line geometries
            max_distance_km: Maximum distance to consider for trail access

        Returns:
            GeoDataFrame with trail accessibility metrics
        """
        self.logger.info(f"Calculating trail accessibility for {len(origin_points)} points")

        try:
            # Convert origin points to GeoDataFrame
            origin_gdf = gpd.GeoDataFrame({
                'geometry': [Point(lon, lat) for lat, lon in origin_points]
            }, crs='EPSG:4326')

            # Calculate distance to nearest trail
            distances = []
            nearest_trails = []

            for _, origin in origin_gdf.iterrows():
                origin_geom = origin.geometry

                # Find minimum distance to any trail segment
                min_distance = float('inf')
                nearest_trail = None

                for _, trail in trail_network.iterrows():
                    trail_geom = trail.geometry
                    distance = origin_geom.distance(trail_geom)

                    if distance < min_distance:
                        min_distance = distance
                        nearest_trail = trail_geom

                distances.append(min_distance * 111000)  # Convert to meters
                nearest_trails.append(nearest_trail)

            # Create result GeoDataFrame
            result_gdf = origin_gdf.copy()
            result_gdf['nearest_trail_distance_m'] = distances
            result_gdf['nearest_trail_geom'] = nearest_trails

            # Calculate accessibility score (closer = higher score)
            result_gdf['trail_accessibility_score'] = [
                max(0, 100 - (dist / 1000)) for dist in distances  # 1km = 100 points
            ]

            self.logger.info(f"Trail accessibility calculated for {len(result_gdf)} points")
            return result_gdf

        except Exception as e:
            self.logger.error(f"Trail accessibility calculation failed: {e}")
            raise

    def park_accessibility(
        self,
        origin_points: List[tuple[float, float]],
        parks: gpd.GeoDataFrame,
        max_drive_time_minutes: int = 30
    ) -> gpd.GeoDataFrame:
        """Calculate park accessibility from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            parks: GeoDataFrame with park polygon geometries
            max_drive_time_minutes: Maximum drive time to consider

        Returns:
            GeoDataFrame with park accessibility metrics
        """
        self.logger.info(f"Calculating park accessibility for {len(origin_points)} points")

        try:
            # Convert origin points to GeoDataFrame
            origin_gdf = gpd.GeoDataFrame({
                'geometry': [Point(lon, lat) for lat, lon in origin_points]
            }, crs='EPSG:4326')

            # Calculate distance to nearest park
            distances = []
            nearest_parks = []

            for _, origin in origin_gdf.iterrows():
                origin_geom = origin.geometry

                # Find minimum distance to any park
                min_distance = float('inf')
                nearest_park = None

                for _, park in parks.iterrows():
                    park_geom = park.geometry
                    distance = origin_geom.distance(park_geom)

                    if distance < min_distance:
                        min_distance = distance
                        nearest_park = park_geom

                distances.append(min_distance * 111000)  # Convert to meters
                nearest_parks.append(nearest_park)

            # Create result GeoDataFrame
            result_gdf = origin_gdf.copy()
            result_gdf['nearest_park_distance_m'] = distances
            result_gdf['nearest_park_geom'] = nearest_parks

            # Calculate accessibility score (closer = higher score)
            result_gdf['park_accessibility_score'] = [
                max(0, 100 - (dist / 5000)) for dist in distances  # 5km = 100 points
            ]

            self.logger.info(f"Park accessibility calculated for {len(result_gdf)} points")
            return result_gdf

        except Exception as e:
            self.logger.error(f"Park accessibility calculation failed: {e}")
            raise

    def water_accessibility(
        self,
        origin_points: List[tuple[float, float]],
        water_bodies: gpd.GeoDataFrame,
        max_distance_km: float = 10.0
    ) -> gpd.GeoDataFrame:
        """Calculate water body accessibility from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            water_bodies: GeoDataFrame with water body geometries
            max_distance_km: Maximum distance to consider

        Returns:
            GeoDataFrame with water accessibility metrics
        """
        self.logger.info(f"Calculating water accessibility for {len(origin_points)} points")

        try:
            # Convert origin points to GeoDataFrame
            origin_gdf = gpd.GeoDataFrame({
                'geometry': [Point(lon, lat) for lat, lon in origin_points]
            }, crs='EPSG:4326')

            # Calculate distance to nearest water body
            distances = []
            nearest_water = []

            for _, origin in origin_gdf.iterrows():
                origin_geom = origin.geometry

                # Find minimum distance to any water body
                min_distance = float('inf')
                nearest_body = None

                for _, water in water_bodies.iterrows():
                    water_geom = water.geometry
                    distance = origin_geom.distance(water_geom)

                    if distance < min_distance:
                        min_distance = distance
                        nearest_body = water_geom

                distances.append(min_distance * 111000)  # Convert to meters
                nearest_water.append(nearest_body)

            # Create result GeoDataFrame
            result_gdf = origin_gdf.copy()
            result_gdf['nearest_water_distance_m'] = distances
            result_gdf['nearest_water_geom'] = nearest_water

            # Calculate accessibility score
            result_gdf['water_accessibility_score'] = [
                max(0, 100 - (dist / 10000)) for dist in distances  # 10km = 100 points
            ]

            self.logger.info(f"Water accessibility calculated for {len(result_gdf)} points")
            return result_gdf

        except Exception as e:
            self.logger.error(f"Water accessibility calculation failed: {e}")
            raise

    def ski_accessibility(
        self,
        origin_points: List[tuple[float, float]],
        ski_areas: gpd.GeoDataFrame,
        transit_feeds: Optional[gpd.GeoDataFrame] = None
    ) -> gpd.GeoDataFrame:
        """Calculate ski area accessibility from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            ski_areas: GeoDataFrame with ski area geometries
            transit_feeds: Optional transit data for ski bus routes

        Returns:
            GeoDataFrame with ski accessibility metrics
        """
        self.logger.info(f"Calculating ski accessibility for {len(origin_points)} points")

        try:
            # Convert origin points to GeoDataFrame
            origin_gdf = gpd.GeoDataFrame({
                'geometry': [Point(lon, lat) for lat, lon in origin_points]
            }, crs='EPSG:4326')

            # Calculate distance to nearest ski area
            distances = []
            nearest_ski = []

            for _, origin in origin_gdf.iterrows():
                origin_geom = origin.geometry

                # Find minimum distance to any ski area
                min_distance = float('inf')
                nearest_area = None

                for _, ski in ski_areas.iterrows():
                    ski_geom = ski.geometry
                    distance = origin_geom.distance(ski_geom)

                    if distance < min_distance:
                        min_distance = distance
                        nearest_area = ski_geom

                distances.append(min_distance * 111000)  # Convert to meters
                nearest_ski.append(nearest_area)

            # Calculate ski bus accessibility if transit data available
            ski_bus_scores = []
            if transit_feeds is not None:
                # Simplified ski bus accessibility calculation
                for distance in distances:
                    # Assume ski bus accessibility if within reasonable distance
                    ski_bus_score = 100 if distance < 50000 else 0  # 50km threshold
                    ski_bus_scores.append(ski_bus_score)
            else:
                ski_bus_scores = [0] * len(origin_points)

            # Create result GeoDataFrame
            result_gdf = origin_gdf.copy()
            result_gdf['nearest_ski_distance_m'] = distances
            result_gdf['nearest_ski_geom'] = nearest_ski
            result_gdf['ski_bus_accessibility'] = ski_bus_scores

            # Calculate overall ski accessibility score
            result_gdf['ski_accessibility_score'] = [
                min(100, (100 - (dist / 1000)) + bus_score) for dist, bus_score in zip(distances, ski_bus_scores)
            ]

            self.logger.info(f"Ski accessibility calculated for {len(result_gdf)} points")
            return result_gdf

        except Exception as e:
            self.logger.error(f"Ski accessibility calculation failed: {e}")
            raise

    def trail_miles_per_capita(
        self,
        msa_bounds: Tuple[float, float, float, float],
        trail_network: gpd.GeoDataFrame,
        population: int
    ) -> float:
        """Calculate trail miles per capita for an MSA.

        Args:
            msa_bounds: MSA bounding box (min_lon, min_lat, max_lon, max_lat)
            trail_network: GeoDataFrame with trail geometries
            population: MSA population

        Returns:
            Trail miles per capita
        """
        try:
            # Calculate total trail length in meters
            total_trail_length_m = 0

            for _, trail in trail_network.iterrows():
                trail_geom = trail.geometry
                if trail_geom.geom_type == 'LineString':
                    total_trail_length_m += trail_geom.length
                elif trail_geom.geom_type == 'MultiLineString':
                    for line in trail_geom.geoms:
                        total_trail_length_m += line.length

            # Convert to miles
            total_trail_length_miles = total_trail_length_m * 0.000621371

            # Calculate per capita
            trail_per_capita = total_trail_length_miles / population if population > 0 else 0

            self.logger.info(f"Trail miles per capita: {trail_per_capita:.3f}")
            return trail_per_capita

        except Exception as e:
            self.logger.error(f"Trail miles per capita calculation failed: {e}")
            return 0.0

    def public_land_accessibility(
        self,
        origin_points: List[tuple[float, float]],
        public_lands: gpd.GeoDataFrame,
        max_drive_time_minutes: int = 30
    ) -> gpd.GeoDataFrame:
        """Calculate public land accessibility from origin points.

        Args:
            origin_points: List of (lat, lon) coordinate tuples
            public_lands: GeoDataFrame with public land polygons
            max_drive_time_minutes: Maximum drive time to consider

        Returns:
            GeoDataFrame with public land accessibility metrics
        """
        self.logger.info(f"Calculating public land accessibility for {len(origin_points)} points")

        try:
            # Convert origin points to GeoDataFrame
            origin_gdf = gpd.GeoDataFrame({
                'geometry': [Point(lon, lat) for lat, lon in origin_points]
            }, crs='EPSG:4326')

            # Calculate total public land area within drive time
            public_land_areas = []

            for _, origin in origin_gdf.iterrows():
                origin_geom = origin.geometry

                # Create buffer representing drive time area (simplified)
                buffer_distance_km = (30 * 50) / 60  # Assume 50 km/h average speed
                buffer = origin_geom.buffer(buffer_distance_km / 111)  # Convert to degrees

                # Calculate intersection with public lands
                total_public_area = 0

                for _, land in public_lands.iterrows():
                    land_geom = land.geometry
                    if buffer.intersects(land_geom):
                        intersection = buffer.intersection(land_geom)
                        total_public_area += intersection.area * 111 * 111  # Convert to km²

                public_land_areas.append(total_public_area)

            # Create result GeoDataFrame
            result_gdf = origin_gdf.copy()
            result_gdf['public_land_area_km2'] = public_land_areas

            # Calculate accessibility score (more public land = higher score)
            max_area = max(public_land_areas) if public_land_areas else 1
            result_gdf['public_land_accessibility_score'] = [
                min(area / max_area * 100, 100) for area in public_land_areas
            ]

            self.logger.info(f"Public land accessibility calculated for {len(result_gdf)} points")
            return result_gdf

        except Exception as e:
            self.logger.error(f"Public land accessibility calculation failed: {e}")
            raise


def trail_accessibility(
    origin_points: List[tuple[float, float]],
    trail_network: gpd.GeoDataFrame,
    max_distance_km: float = 5.0
) -> gpd.GeoDataFrame:
    """Calculate trail accessibility from origin points.

    Args:
        origin_points: List of (lat, lon) coordinate tuples
        trail_network: GeoDataFrame with trail geometries
        max_distance_km: Maximum distance to consider

    Returns:
        GeoDataFrame with trail accessibility metrics
    """
    analyzer = RecreationAnalyzer()
    return analyzer.trail_accessibility(origin_points, trail_network, max_distance_km)


def park_accessibility(
    origin_points: List[tuple[float, float]],
    parks: gpd.GeoDataFrame,
    max_drive_time_minutes: int = 30
) -> gpd.GeoDataFrame:
    """Calculate park accessibility from origin points.

    Args:
        origin_points: List of (lat, lon) coordinate tuples
        parks: GeoDataFrame with park geometries
        max_drive_time_minutes: Maximum drive time to consider

    Returns:
        GeoDataFrame with park accessibility metrics
    """
    analyzer = RecreationAnalyzer()
    return analyzer.park_accessibility(origin_points, parks, max_drive_time_minutes)
