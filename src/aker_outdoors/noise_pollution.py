"""Noise pollution analysis for transportation infrastructure proximity."""

from __future__ import annotations

from typing import Dict, Optional

import geopandas as gpd

from aker_core.logging import get_logger

from .models import NoiseLevel


class NoiseAnalyzer:
    """Analyzer for transportation noise pollution assessment."""

    def __init__(self):
        """Initialize noise analyzer."""
        self.logger = get_logger(__name__)

        # Noise decay models by transportation type
        self.noise_decay_models = {
            "highway": {
                "decay_rate": 0.5,  # dB per doubling of distance
                "reference_distance": 15.0,  # meters
                "reference_level": 75.0  # dB at reference distance
            },
            "rail": {
                "decay_rate": 0.6,
                "reference_distance": 15.0,
                "reference_level": 80.0
            },
            "airport": {
                "decay_rate": 0.4,
                "reference_distance": 100.0,
                "reference_level": 85.0
            }
        }

    def highway_proximity(
        self,
        parcels: gpd.GeoDataFrame,
        highways: gpd.GeoDataFrame,
        max_distance_km: float = 1.0
    ) -> gpd.GeoDataFrame:
        """Calculate highway proximity impact on parcels.

        Args:
            parcels: GeoDataFrame with parcel geometries
            highways: GeoDataFrame with highway line geometries
            max_distance_km: Maximum distance to consider for noise impact

        Returns:
            GeoDataFrame with noise impact metrics
        """
        self.logger.info(f"Analyzing highway proximity for {len(parcels)} parcels")

        try:
            # Calculate distance from each parcel to nearest highway
            parcel_centroids = parcels.geometry.centroid

            min_distances = []
            max_noise_levels = []

            for centroid in parcel_centroids:
                # Find minimum distance to any highway segment
                distances = highways.geometry.distance(centroid)
                min_distance = distances.min() * 1000  # Convert to meters

                min_distances.append(min_distance)

                # Calculate noise level at this distance
                noise_level = self._calculate_noise_level(min_distance, "highway")
                max_noise_levels.append(noise_level)

            # Add noise metrics to parcels
            parcels_copy = parcels.copy()
            parcels_copy['highway_distance_m'] = min_distances
            parcels_copy['highway_noise_db'] = max_noise_levels
            parcels_copy['highway_noise_level'] = [
                self._classify_noise_level(noise) for noise in max_noise_levels
            ]

            # Calculate proximity index (lower distance = higher impact)
            max_distance_m = max_distance_km * 1000
            parcels_copy['highway_proximity_index'] = [
                max(0, 100 - (dist / max_distance_m) * 100) for dist in min_distances
            ]

            self.logger.info(f"Highway proximity analysis complete for {len(parcels)} parcels")
            return parcels_copy

        except Exception as e:
            self.logger.error(f"Highway proximity analysis failed: {e}")
            raise

    def rail_proximity(
        self,
        parcels: gpd.GeoDataFrame,
        rail_lines: gpd.GeoDataFrame,
        max_distance_km: float = 0.5
    ) -> gpd.GeoDataFrame:
        """Calculate rail proximity impact on parcels.

        Args:
            parcels: GeoDataFrame with parcel geometries
            rail_lines: GeoDataFrame with rail line geometries
            max_distance_km: Maximum distance to consider for noise impact

        Returns:
            GeoDataFrame with rail noise metrics
        """
        self.logger.info(f"Analyzing rail proximity for {len(parcels)} parcels")

        try:
            # Calculate distance from each parcel to nearest rail line
            parcel_centroids = parcels.geometry.centroid

            min_distances = []
            max_noise_levels = []

            for centroid in parcel_centroids:
                # Find minimum distance to any rail segment
                distances = rail_lines.geometry.distance(centroid)
                min_distance = distances.min() * 1000  # Convert to meters

                min_distances.append(min_distance)

                # Calculate noise level at this distance
                noise_level = self._calculate_noise_level(min_distance, "rail")
                max_noise_levels.append(noise_level)

            # Add noise metrics to parcels
            parcels_copy = parcels.copy()
            parcels_copy['rail_distance_m'] = min_distances
            parcels_copy['rail_noise_db'] = max_noise_levels
            parcels_copy['rail_noise_level'] = [
                self._classify_noise_level(noise) for noise in max_noise_levels
            ]

            # Calculate proximity index
            max_distance_m = max_distance_km * 1000
            parcels_copy['rail_proximity_index'] = [
                max(0, 100 - (dist / max_distance_m) * 100) for dist in min_distances
            ]

            self.logger.info(f"Rail proximity analysis complete for {len(parcels)} parcels")
            return parcels_copy

        except Exception as e:
            self.logger.error(f"Rail proximity analysis failed: {e}")
            raise

    def airport_noise_zones(
        self,
        parcels: gpd.GeoDataFrame,
        noise_zones: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Analyze airport noise zone impacts on parcels.

        Args:
            parcels: GeoDataFrame with parcel geometries
            noise_zones: GeoDataFrame with airport noise contour polygons

        Returns:
            GeoDataFrame with airport noise zone classifications
        """
        self.logger.info(f"Analyzing airport noise zones for {len(parcels)} parcels")

        try:
            # Find which noise zones intersect with parcels
            noise_impact = []

            for _, parcel in parcels.iterrows():
                parcel_geom = parcel.geometry

                # Check intersection with noise zones
                max_noise_level = 0
                affected_zones = []

                for _, zone in noise_zones.iterrows():
                    if parcel_geom.intersects(zone.geometry):
                        # Get noise level from zone attributes
                        noise_db = zone.get('noise_db', 0)
                        max_noise_level = max(max_noise_level, noise_db)
                        affected_zones.append(zone.get('zone_id', 'unknown'))

                noise_impact.append({
                    'airport_noise_db': max_noise_level,
                    'airport_noise_level': self._classify_noise_level(max_noise_level),
                    'affected_noise_zones': affected_zones
                })

            # Add to parcels
            parcels_copy = parcels.copy()
            for i, impact in enumerate(noise_impact):
                parcels_copy.at[i, 'airport_noise_db'] = impact['airport_noise_db']
                parcels_copy.at[i, 'airport_noise_level'] = impact['airport_noise_level']
                parcels_copy.at[i, 'affected_noise_zones'] = impact['affected_noise_zones']

            self.logger.info(f"Airport noise zone analysis complete for {len(parcels)} parcels")
            return parcels_copy

        except Exception as e:
            self.logger.error(f"Airport noise zone analysis failed: {e}")
            raise

    def composite_noise_index(
        self,
        parcels: gpd.GeoDataFrame,
        weights: Optional[Dict[str, float]] = None
    ) -> gpd.GeoDataFrame:
        """Calculate composite noise pollution index for parcels.

        Args:
            parcels: GeoDataFrame with individual noise metrics
            weights: Optional weights for different noise sources

        Returns:
            GeoDataFrame with composite noise index
        """
        default_weights = {
            "highway": 0.4,
            "rail": 0.3,
            "airport": 0.3
        }
        weights = weights or default_weights

        self.logger.info("Calculating composite noise index")

        try:
            # Calculate weighted noise index
            noise_indices = []

            for _, parcel in parcels.iterrows():
                # Get noise levels for each source
                highway_noise = parcel.get('highway_noise_db', 0)
                rail_noise = parcel.get('rail_noise_db', 0)
                airport_noise = parcel.get('airport_noise_db', 0)

                # Convert dB to 0-100 index (higher dB = higher index)
                highway_index = min(highway_noise / 85.0 * 100, 100)  # 85 dB max
                rail_index = min(rail_noise / 90.0 * 100, 100)       # 90 dB max
                airport_index = min(airport_noise / 95.0 * 100, 100)  # 95 dB max

                # Weighted combination
                composite_index = (
                    highway_index * weights["highway"] +
                    rail_index * weights["rail"] +
                    airport_index * weights["airport"]
                )

                noise_indices.append(composite_index)

            parcels_copy = parcels.copy()
            parcels_copy['composite_noise_index'] = noise_indices
            parcels_copy['noise_level'] = [
                self._classify_noise_level(index) for index in noise_indices
            ]

            self.logger.info(f"Composite noise index calculated for {len(parcels)} parcels")
            return parcels_copy

        except Exception as e:
            self.logger.error(f"Composite noise index calculation failed: {e}")
            raise

    def _calculate_noise_level(self, distance_m: float, source_type: str) -> float:
        """Calculate noise level at a given distance from source."""
        if distance_m <= 0:
            return 0.0

        model = self.noise_decay_models.get(source_type)
        if not model:
            return 0.0

        # Simple noise decay model: L(d) = L_ref - decay_rate * log2(d / d_ref)
        import math
        distance_ratio = distance_m / model["reference_distance"]

        if distance_ratio <= 1:
            return model["reference_level"]

        noise_level = (
            model["reference_level"] -
            model["decay_rate"] * math.log2(distance_ratio)
        )

        return max(noise_level, 0.0)  # Minimum 0 dB

    def _classify_noise_level(self, db_level: float) -> NoiseLevel:
        """Classify noise level into categories."""
        if db_level < 50:
            return NoiseLevel.QUIET
        elif db_level < 65:
            return NoiseLevel.MODERATE
        elif db_level < 80:
            return NoiseLevel.LOUD
        elif db_level < 95:
            return NoiseLevel.VERY_LOUD
        else:
            return NoiseLevel.EXTREME


def highway_proximity(
    parcels: gpd.GeoDataFrame,
    highways: gpd.GeoDataFrame,
    max_distance_km: float = 1.0
) -> gpd.GeoDataFrame:
    """Calculate highway proximity impact on parcels.

    Args:
        parcels: GeoDataFrame with parcel geometries
        highways: GeoDataFrame with highway line geometries
        max_distance_km: Maximum distance to consider for noise impact

    Returns:
        GeoDataFrame with noise impact metrics
    """
    analyzer = NoiseAnalyzer()
    return analyzer.highway_proximity(parcels, highways, max_distance_km)
