"""Tests for terrain analysis utilities."""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import LineString, Polygon, box

from aker_geo.terrain import (
    DigitalElevationModel,
    analyze_noise,
    analyze_viewshed,
    assess_parcel_buffers,
    combine_overlay_results,
    compute_constraint_scores,
    load_nhd_waterways,
    load_usgs_dem,
    slope_percent,
    waterway,
)


@pytest.fixture
def planar_dem() -> DigitalElevationModel:
    grid = np.add.outer(np.arange(5), np.arange(5)).astype(float)
    return DigitalElevationModel(grid, origin=(0.0, 0.0), pixel_size=(30.0, 30.0), crs="EPSG:3857")


@pytest.fixture
def parcel_gdf() -> gpd.GeoDataFrame:
    parcel = box(0, -150, 150, 0)
    return gpd.GeoDataFrame({"parcel_id": ["A"]}, geometry=[parcel], crs="EPSG:3857")


class TestSlopeAnalysis:
    def test_slope_statistics_on_planar_surface(
        self, planar_dem: DigitalElevationModel, parcel_gdf: gpd.GeoDataFrame
    ):
        result = slope_percent(parcel_gdf, planar_dem)

        slope_ratio = math.sqrt(2.0) / 30.0
        expected_percent = slope_ratio * 100.0
        stats = result.iloc[0]
        assert pytest.approx(stats["slope_mean_pct"], rel=1e-2) == expected_percent
        assert pytest.approx(stats["slope_max_pct"], rel=1e-2) == expected_percent
        assert stats["slope_primary_severity"] == "flat"
        assert stats["slope_constrained_area_pct"] == pytest.approx(0.0)
        assert stats["slope_confidence"] == pytest.approx(1.0)
        report = planar_dem.quality_report()
        assert report["pixel_size"] == (30.0, 30.0)
        assert report["valid_ratio"] == pytest.approx(1.0)


class TestWaterwayBuffers:
    def test_waterway_buffer_generation_and_assessment(self, parcel_gdf: gpd.GeoDataFrame):
        waterways = gpd.GeoDataFrame(
            {"FType": ["StreamRiver"], "geometry": [LineString([(0, -500), (0, 500)])]},
            crs="EPSG:3857",
        )
        buffers = waterway(waterways, distance_range=(100, 300))
        assert len(buffers) == 3
        assert set(buffers["distance_ft"]) == {100.0, 200.0, 300.0}

        assessment = assess_parcel_buffers(parcel_gdf, buffers)
        stats = assessment.iloc[0]
        impacts = stats["buffer_distance_impacts"]
        assert isinstance(impacts, dict)
        assert set(impacts) == {100.0, 200.0, 300.0}
        assert stats["buffer_impacted_pct"] > 0
        assert stats["buffer_severity"] in {"low", "medium", "high"}
        assert "streamriver" in [ftype.lower() for ftype in stats["buffer_feature_types"]]


class TestOverlayAnalysis:
    @pytest.fixture
    def overlay_parcels(self) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {"parcel_id": ["A"]},
            geometry=[Polygon([(-150, -150), (150, -150), (150, 0), (-150, 0)])],
            crs="EPSG:3857",
        )

    def test_noise_and_viewshed_analysis(self, overlay_parcels: gpd.GeoDataFrame):
        noise_overlay = gpd.GeoDataFrame(
            {
                "decibel": [70.0],
                "source": ["airport"],
                "geometry": [Polygon([(-60, -150), (60, -150), (60, -30), (-60, -30)])],
            },
            crs="EPSG:3857",
        )
        viewshed_overlay = gpd.GeoDataFrame(
            {
                "impact": [1.0],
                "source": ["scenic"],
                "geometry": [Polygon([(-150, -90), (150, -90), (150, 0), (-150, 0)])],
            },
            crs="EPSG:3857",
        )

        noise = analyze_noise(overlay_parcels, noise_overlay)
        viewshed = analyze_viewshed(overlay_parcels, viewshed_overlay)
        combined = combine_overlay_results(overlay_parcels, noise=noise, viewshed=viewshed)
        row = combined.iloc[0]

        assert row["noise_overlay_pct"] > 0
        assert row["viewshed_overlay_pct"] > 0
        assert (
            row["overlay_constraint_score"]
            >= max(row["noise_overlay_pct"], row["viewshed_overlay_pct"]) / 2.0
        )

    def test_constraint_scoring_pipeline(
        self,
        planar_dem: DigitalElevationModel,
        parcel_gdf: gpd.GeoDataFrame,
        overlay_parcels: gpd.GeoDataFrame,
    ):
        slope = slope_percent(parcel_gdf, planar_dem)

        waterways = gpd.GeoDataFrame(
            {"feature_type": ["river"], "geometry": [LineString([(0, -500), (0, 500)])]},
            crs="EPSG:3857",
        )
        buffers = waterway(waterways, distance_range=(100, 300))
        buffer_stats = assess_parcel_buffers(parcel_gdf, buffers)

        noise_overlay = gpd.GeoDataFrame(
            {
                "decibel": [65.0],
                "source": ["rail"],
                "geometry": [Polygon([(-50, -150), (50, -150), (50, -50), (-50, -50)])],
            },
            crs="EPSG:3857",
        )
        noise = analyze_noise(overlay_parcels, noise_overlay)
        combined = combine_overlay_results(overlay_parcels, noise=noise)

        scored = compute_constraint_scores(
            parcel_gdf, slope=slope, buffers=buffer_stats, overlays=combined
        )
        result_row = scored.iloc[0]
        assert {"slope_pct", "buffer_pct", "noise_overlay_pct", "constraint_score"}.issubset(
            result_row.index
        )
        assert 0.0 <= result_row["constraint_score"] <= 100.0


class TestDataIntegration:
    def test_load_nhd_waterways_roundtrip(self, tmp_path: Path):
        waterways = gpd.GeoDataFrame(
            {
                "FType": ["StreamRiver"],
                "geometry": [LineString([(0, 0), (0, 1)])],
            },
            crs="EPSG:4326",
        )
        gpkg_path = tmp_path / "nhd.gpkg"
        waterways.to_file(gpkg_path, layer="water", driver="GPKG")

        loaded = load_nhd_waterways(gpkg_path, layer="water")
        assert "feature_type" in loaded.columns
        assert loaded.crs is not None

    def test_load_usgs_dem_optional(self, tmp_path: Path):
        rasterio = pytest.importorskip("rasterio")
        dem_array = np.arange(25, dtype=float).reshape(5, 5)
        transform = rasterio.transform.from_origin(0.0, 0.0, 30.0, 30.0)
        tif_path = tmp_path / "dem.tif"
        with rasterio.open(
            tif_path,
            "w",
            driver="GTiff",
            width=dem_array.shape[1],
            height=dem_array.shape[0],
            count=1,
            dtype="float64",
            crs="EPSG:3857",
            transform=transform,
        ) as dst:
            dst.write(dem_array, 1)

        dem = load_usgs_dem(tif_path)
        report = dem.quality_report()
        assert report["crs"] == "EPSG:3857"
        assert report["valid_ratio"] == pytest.approx(1.0)
