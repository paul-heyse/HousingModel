"""Air quality analysis for PM2.5 monitoring and seasonal variation."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from shapely.geometry import Point

from aker_core.logging import get_logger

from ..connectors.base import DataConnector
from .models import AirQualityLevel


class EPAAirNowConnector(DataConnector):
    """Connector for EPA AirNow air quality monitoring data."""

    def __init__(self, **kwargs):
        """Initialize EPA AirNow connector."""
        super().__init__(
            name="epa_airnow",
            base_url="https://www.airnowapi.org/aq",
            output_schema={
                "station_id": "string",
                "station_name": "string",
                "latitude": "float64",
                "longitude": "float64",
                "pm25_concentration": "float64",
                "aqi": "int64",
                "category": "string",
                "measurement_date": "datetime64[ns]",
                "reporting_area": "string",
                "state_code": "string",
                "collected_at": "datetime64[ns]",
            },
            **kwargs
        )
        self.api_key = kwargs.get("api_key")

    def _fetch_raw_data(
        self,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> pd.DataFrame:
        """Fetch air quality data from EPA AirNow API."""
        # EPA AirNow API endpoint
        endpoint = "/observation/latLong/current/"

        # Build parameters
        params = {
            "format": "application/json",
            "latitude": kwargs.get("latitude", 40.7128),  # Default to NYC
            "longitude": kwargs.get("longitude", -74.0060),
            "distance": kwargs.get("distance", 25),  # 25 mile radius
        }

        if self.api_key:
            params["API_KEY"] = self.api_key

        response = self._make_request(endpoint, params=params)

        if response.status_code != 200:
            self.logger.error(f"EPA AirNow API error: {response.status_code}")
            return pd.DataFrame()

        data = response.json()

        # Convert to DataFrame
        records = []
        for item in data:
            if item.get("ParameterName") == "PM2.5":
                record = {
                    "station_id": item.get("SiteCode", ""),
                    "station_name": item.get("SiteName", ""),
                    "latitude": float(item.get("Latitude", 0)),
                    "longitude": float(item.get("Longitude", 0)),
                    "pm25_concentration": float(item.get("Concentration", 0)),
                    "aqi": int(item.get("AQI", 0)),
                    "category": item.get("Category", {}).get("Name", ""),
                    "measurement_date": pd.to_datetime(item.get("DateObserved", "")),
                    "reporting_area": item.get("ReportingArea", ""),
                    "state_code": item.get("StateCode", ""),
                    "collected_at": pd.Timestamp.now(),
                }
                records.append(record)

        return pd.DataFrame(records)

    def _transform_to_dataframe(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Transform EPA AirNow data to standardized format."""
        df = super()._transform_to_dataframe(raw_data)

        # Add metadata
        df["source_system"] = "epa_airnow_api"
        df["collected_at"] = pd.Timestamp.now()

        return df


class AirQualityAnalyzer:
    """Analyzer for air quality data and seasonal variation."""

    def __init__(self):
        """Initialize air quality analyzer."""
        self.logger = get_logger(__name__)

    def pm25_variation(
        self,
        air_quality_data: pd.DataFrame,
        seasons: List[str] = None,
        aggregation_level: str = "monthly"
    ) -> Dict[str, float]:
        """Calculate PM2.5 air quality seasonal and temporal variation.

        Args:
            air_quality_data: DataFrame with PM2.5 concentration data
            seasons: List of seasons to analyze ("spring", "summer", "fall", "winter")
            aggregation_level: Time aggregation level ("daily", "weekly", "monthly")

        Returns:
            Dictionary with variation metrics
        """
        if seasons is None:
            seasons = ["spring", "summer", "fall", "winter"]

        self.logger.info(f"Analyzing PM2.5 variation for {len(air_quality_data)} records")

        try:
            # Ensure we have the required columns
            if 'pm25_concentration' not in air_quality_data.columns:
                self.logger.warning("PM2.5 concentration data not found")
                return {}

            # Filter for valid PM2.5 data
            valid_data = air_quality_data.dropna(subset=['pm25_concentration'])
            valid_data = valid_data[valid_data['pm25_concentration'] > 0]

            if len(valid_data) == 0:
                self.logger.warning("No valid PM2.5 data found")
                return {}

            # Calculate seasonal statistics
            seasonal_stats = {}

            for season in seasons:
                season_data = self._get_season_data(valid_data, season)

                if len(season_data) > 0:
                    seasonal_stats[season] = {
                        "mean": season_data['pm25_concentration'].mean(),
                        "median": season_data['pm25_concentration'].median(),
                        "std": season_data['pm25_concentration'].std(),
                        "min": season_data['pm25_concentration'].min(),
                        "max": season_data['pm25_concentration'].max(),
                        "count": len(season_data)
                    }

            # Calculate overall variation metrics
            overall_stats = {
                "mean": valid_data['pm25_concentration'].mean(),
                "std": valid_data['pm25_concentration'].std(),
                "cv": valid_data['pm25_concentration'].std() / valid_data['pm25_concentration'].mean() if valid_data['pm25_concentration'].mean() > 0 else 0,
                "data_points": len(valid_data)
            }

            # Calculate seasonal variation index (coefficient of variation across seasons)
            if len(seasonal_stats) > 1:
                seasonal_means = [stats["mean"] for stats in seasonal_stats.values()]
                seasonal_variation = np.std(seasonal_means) / np.mean(seasonal_means) if np.mean(seasonal_means) > 0 else 0
            else:
                seasonal_variation = 0

            result = {
                "overall_stats": overall_stats,
                "seasonal_stats": seasonal_stats,
                "seasonal_variation": seasonal_variation,
                "data_quality_score": self._calculate_data_quality_score(valid_data)
            }

            self.logger.info(f"PM2.5 variation analysis complete: {len(valid_data)} data points, {seasonal_variation".3f"} seasonal variation")
            return result

        except Exception as e:
            self.logger.error(f"PM2.5 variation analysis failed: {e}")
            return {"error": str(e)}

    def _get_season_data(self, data: pd.DataFrame, season: str) -> pd.DataFrame:
        """Get data for a specific season."""
        # Simple season mapping based on month
        season_months = {
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "fall": [9, 10, 11]
        }

        months = season_months.get(season.lower(), [])
        if not months:
            return pd.DataFrame()

        # Filter data by month
        if 'measurement_date' in data.columns:
            return data[data['measurement_date'].dt.month.isin(months)]
        else:
            return pd.DataFrame()

    def _calculate_data_quality_score(self, data: pd.DataFrame) -> float:
        """Calculate data quality score based on completeness and consistency."""
        total_records = len(data)

        # Completeness score (percentage of non-null values)
        completeness_score = data['pm25_concentration'].notna().sum() / total_records * 100

        # Range reasonableness score
        if 'pm25_concentration' in data.columns:
            pm25_values = data['pm25_concentration'].dropna()
            if len(pm25_values) > 0:
                # Check for reasonable PM2.5 range (0-500 μg/m³)
                reasonable_range = ((pm25_values >= 0) & (pm25_values <= 500)).sum() / len(pm25_values) * 100
            else:
                reasonable_range = 0
        else:
            reasonable_range = 0

        # Combine scores (weighted average)
        quality_score = (completeness_score * 0.6) + (reasonable_range * 0.4)

        return quality_score

    def classify_air_quality(self, pm25_concentration: float) -> AirQualityLevel:
        """Classify PM2.5 concentration into air quality levels."""
        if pm25_concentration <= 12:
            return AirQualityLevel.GOOD
        elif pm25_concentration <= 35.4:
            return AirQualityLevel.MODERATE
        elif pm25_concentration <= 55.4:
            return AirQualityLevel.UNHEALTHY_SENSITIVE
        elif pm25_concentration <= 150.4:
            return AirQualityLevel.UNHEALTHY
        elif pm25_concentration <= 250.4:
            return AirQualityLevel.VERY_UNHEALTHY
        else:
            return AirQualityLevel.HAZARDOUS

    def air_quality_trend_analysis(
        self,
        air_quality_data: pd.DataFrame,
        time_window_days: int = 365
    ) -> Dict[str, float]:
        """Analyze air quality trends over time.

        Args:
            air_quality_data: DataFrame with PM2.5 data
            time_window_days: Analysis window in days

        Returns:
            Dictionary with trend analysis results
        """
        try:
            if 'pm25_concentration' not in air_quality_data.columns:
                return {"error": "PM2.5 concentration data not found"}

            # Sort by date
            sorted_data = air_quality_data.sort_values('measurement_date')

            # Calculate rolling statistics
            rolling_mean = sorted_data['pm25_concentration'].rolling(window=time_window_days, min_periods=30).mean()
            rolling_std = sorted_data['pm25_concentration'].rolling(window=time_window_days, min_periods=30).std()

            # Calculate trend (linear regression slope)
            valid_data = sorted_data.dropna(subset=['pm25_concentration'])
            if len(valid_data) > 30:
                # Simple trend calculation using numpy
                x = np.arange(len(valid_data))
                y = valid_data['pm25_concentration'].values
                slope = np.polyfit(x, y, 1)[0]
                trend_direction = "improving" if slope < 0 else "worsening" if slope > 0 else "stable"
            else:
                slope = 0
                trend_direction = "insufficient_data"

            return {
                "trend_slope": slope,
                "trend_direction": trend_direction,
                "rolling_mean_final": rolling_mean.iloc[-1] if len(rolling_mean) > 0 else None,
                "rolling_std_final": rolling_std.iloc[-1] if len(rolling_std) > 0 else None,
                "data_points": len(valid_data),
                "analysis_window_days": time_window_days
            }

        except Exception as e:
            self.logger.error(f"Air quality trend analysis failed: {e}")
            return {"error": str(e)}


def pm25_variation(
    air_quality_data: pd.DataFrame,
    seasons: List[str] = None,
    aggregation_level: str = "monthly"
) -> Dict[str, float]:
    """Calculate PM2.5 air quality seasonal and temporal variation.

    Args:
        air_quality_data: DataFrame with PM2.5 concentration data
        seasons: List of seasons to analyze
        aggregation_level: Time aggregation level

    Returns:
        Dictionary with variation metrics
    """
    analyzer = AirQualityAnalyzer()
    return analyzer.pm25_variation(air_quality_data, seasons, aggregation_level)
