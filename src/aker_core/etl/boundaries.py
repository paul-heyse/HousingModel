"""ETL helpers for boundary datasets (TIGERweb, OpenAddresses, Microsoft footprints).

The OpenSpec change *add-boundary-geocoding-integration* formalises how the
platform ingests authoritative boundary data. This module centralises the
connectors, applies geospatial validation, and pushes results into the shared
data lake with lineage metadata.
"""

from __future__ import annotations

import io
import json
import logging
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Iterable, Mapping, MutableMapping, Optional, Sequence

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

from aker_core.cache import Cache, RateLimiter, get_cache
from aker_data.lake import DataLake
from aker_geo.validate import validate_crs, validate_geometry

logger = logging.getLogger(__name__)

TIGERWEB_BASE_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
OPENADDRESSES_BASE_URL = "https://data.openaddresses.io/runs/{run_id}/{dataset}.zip"
MICROSOFT_BUILDINGS_URL = "https://minedbuildings.blob.core.windows.net/global-buildings/{country}.zip"

DEFAULT_TIMEOUT = 60
DEFAULT_GEOMETRY_CRS = "EPSG:4326"


@dataclass(frozen=True)
class TigerwebLayerConfig:
    """Configuration for a TIGERweb feature layer."""

    name: str
    service_path: str
    layer: int
    dataset: str
    where_template: str = "1=1"
    partition_by: Sequence[str] = ()
    cache_ttl: str = "365d"
    requires_state: bool = False


TIGERWEB_LAYERS: Mapping[str, TigerwebLayerConfig] = {
    "states": TigerwebLayerConfig(
        name="states",
        service_path="State_TIGERweb",
        layer=28,
        dataset="boundaries_state",
        partition_by=("STUSPS",),
    ),
    "counties": TigerwebLayerConfig(
        name="counties",
        service_path="Counties_Cartographic",
        layer=2,
        dataset="boundaries_county",
        partition_by=("STATE", "COUNTY"),
    ),
    "tracts": TigerwebLayerConfig(
        name="tracts",
        service_path="Tracts_Blocks",
        layer=2,
        dataset="boundaries_tract",
        partition_by=("STATE", "COUNTY"),
        where_template="STATE='{state_fips}'",
        requires_state=True,
    ),
    "places": TigerwebLayerConfig(
        name="places",
        service_path="Places_CouSub",
        layer=0,
        dataset="boundaries_place",
        partition_by=("STATE",),
        where_template="STATE='{state_fips}'",
        requires_state=True,
    ),
    "zcta5": TigerwebLayerConfig(
        name="zcta5",
        service_path="ZCTA5",
        layer=0,
        dataset="boundaries_zcta",
        partition_by=("ZCTA5",),
    ),
}


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "aker-core-boundaries/1.0"})
    return session


def _resolve_cache(cache: Optional[Cache]) -> Cache:
    return cache or get_cache()


def _prepare_geodataframe(
    features: Iterable[Mapping[str, object]],
    *,
    crs: str = DEFAULT_GEOMETRY_CRS,
    source_id: str,
    attributes_key: str = "attributes",
) -> gpd.GeoDataFrame:
    """Convert an iterable of ArcGIS feature records into a GeoDataFrame."""

    geojson_features: list[dict[str, object]] = []
    for feature in features:
        properties = dict(feature.get(attributes_key, {}))
        geometry = feature.get("geometry")
        geojson_features.append({"geometry": geometry, "properties": properties})

    if not geojson_features:
        return gpd.GeoDataFrame(columns=["geometry", "source_id"], geometry="geometry", crs=crs)

    gdf = gpd.GeoDataFrame.from_features(geojson_features, crs=crs)
    gdf["source_id"] = source_id
    return gdf


def _current_as_of(as_of: Optional[str]) -> str:
    return as_of or datetime.now(UTC).strftime("%Y-%m")


def _ensure_rate_limiter(
    rate_limiter: Optional[RateLimiter],
    token: str,
    *,
    requests_per_minute: int = 120,
    burst_size: int = 30,
) -> RateLimiter:
    return rate_limiter or RateLimiter(token, requests_per_minute=requests_per_minute, burst_size=burst_size)


def load_tigerweb_layer(
    *,
    config: TigerwebLayerConfig,
    where: Optional[str] = None,
    session: Optional[requests.Session] = None,
    base_url: str = TIGERWEB_BASE_URL,
    lake: Optional[DataLake] = None,
    cache: Optional[Cache] = None,
    rate_limiter: Optional[RateLimiter] = None,
    as_of: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Fetch a single TIGERweb feature layer and normalise into a GeoDataFrame."""

    session = session or _default_session()
    cache = _resolve_cache(cache)
    limiter = _ensure_rate_limiter(rate_limiter, f"tigerweb:{config.name}", requests_per_minute=120)

    query_where = where or config.where_template
    params = {"where": query_where, "outFields": "*", "f": "json"}

    request = requests.Request(
        method="GET",
        url=f"{base_url}/{config.service_path}/MapServer/{config.layer}/query",
        params=params,
    )
    prepared = request.prepare()

    limiter._wait_for_token()
    response = cache.fetch(
        prepared.url,
        etl_key=f"tigerweb/{config.name}",
        ttl=config.cache_ttl,
        headers=session.headers,
    )

    payload = response.json()
    features = payload.get("features", [])
    gdf = _prepare_geodataframe(features, crs=DEFAULT_GEOMETRY_CRS, source_id=config.name)

    ingest_ts = datetime.now(UTC)
    gdf["ingested_at"] = ingest_ts
    gdf["layer_name"] = config.name
    gdf["run_where"] = query_where
    gdf["as_of"] = _current_as_of(as_of)

    _run_boundary_validations(gdf, config.name)

    if lake is not None and not gdf.empty:
        lake.write(
            gdf,
            dataset=config.dataset,
            as_of=gdf["as_of"].iloc[0],
            partition_by=list(config.partition_by),
            dataset_type="boundaries",
        )

    logger.info(
        "tigerweb_layer_loaded",
        extra={
            "layer": config.name,
            "records": len(gdf),
            "where": query_where,
        },
    )
    return gdf


def load_tigerweb(
    *,
    layers: Optional[Sequence[str]] = None,
    state_fips: Optional[Sequence[str]] = None,
    as_of: Optional[str] = None,
    base_url: str = TIGERWEB_BASE_URL,
    lake: Optional[DataLake] = None,
    cache: Optional[Cache] = None,
    rate_limiters: Optional[MutableMapping[str, RateLimiter]] = None,
) -> Dict[str, gpd.GeoDataFrame]:
    """Load one or more TIGERweb layers, optionally fan-out by state FIPS."""

    selected_layers = layers or list(TIGERWEB_LAYERS.keys())
    cache = _resolve_cache(cache)
    results: Dict[str, gpd.GeoDataFrame] = {}
    rate_limiters = rate_limiters or {}

    for layer_name in selected_layers:
        if layer_name not in TIGERWEB_LAYERS:
            raise KeyError(f"Unknown TIGERweb layer '{layer_name}'")

        config = TIGERWEB_LAYERS[layer_name]

        if config.requires_state:
            if not state_fips:
                logger.warning(
                    "tigerweb_layer_skipped",
                    extra={"layer": layer_name, "reason": "state_fips_not_provided"},
                )
                continue
            frames: list[gpd.GeoDataFrame] = []
            for fips in state_fips:
                where = config.where_template.format(state_fips=str(fips))
                limiter = rate_limiters.get(layer_name)
                frame = load_tigerweb_layer(
                    config=config,
                    where=where,
                    base_url=base_url,
                    lake=lake,
                    cache=cache,
                    rate_limiter=limiter,
                    as_of=as_of,
                )
                frames.append(frame)
            if frames:
                concatenated = pd.concat(frames, ignore_index=True)
                results[layer_name] = gpd.GeoDataFrame(
                    concatenated,
                    geometry="geometry",
                    crs=DEFAULT_GEOMETRY_CRS,
                )
            else:
                results[layer_name] = gpd.GeoDataFrame(
                    columns=["geometry"], geometry="geometry", crs=DEFAULT_GEOMETRY_CRS
                )
        else:
            limiter = rate_limiters.get(layer_name)
            results[layer_name] = load_tigerweb_layer(
                config=config,
                base_url=base_url,
                lake=lake,
                cache=cache,
                rate_limiter=limiter,
                as_of=as_of,
            )

    return results


def load_openaddresses(
    *,
    run_id: str,
    dataset: str,
    session: Optional[requests.Session] = None,
    base_url: str = OPENADDRESSES_BASE_URL,
    lake: Optional[DataLake] = None,
    lake_dataset: str = "openaddresses",
    cache: Optional[Cache] = None,
    rate_limiter: Optional[RateLimiter] = None,
    as_of: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Download an OpenAddresses zipped CSV and return a deduplicated GeoDataFrame."""

    session = session or _default_session()
    cache = _resolve_cache(cache)
    limiter = _ensure_rate_limiter(rate_limiter, "openaddresses", requests_per_minute=60, burst_size=10)

    url = base_url.format(run_id=run_id, dataset=dataset)
    limiter._wait_for_token()
    response = cache.fetch(url, etl_key=f"openaddresses/{dataset}", ttl="90d", headers=session.headers)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        csv_name = next(name for name in zf.namelist() if name.endswith(".csv"))
        with zf.open(csv_name) as handle:
            frame = pd.read_csv(handle)

    frame.columns = [col.lower() for col in frame.columns]
    dedupe_cols = [col for col in ("hash", "lon", "lat", "source") if col in frame.columns]
    if dedupe_cols:
        frame = frame.drop_duplicates(subset=dedupe_cols)
    else:
        frame = frame.drop_duplicates()

    geometry = _point_geometry_from_frame(frame)
    gdf = gpd.GeoDataFrame(frame, geometry=geometry, crs=DEFAULT_GEOMETRY_CRS)

    ingest_ts = datetime.now(UTC)
    gdf["ingested_at"] = ingest_ts
    gdf["as_of"] = _current_as_of(as_of)
    gdf["source_id"] = "openaddresses"

    _run_boundary_validations(gdf, "openaddresses")

    if lake is not None and not gdf.empty:
        lake.write(
            gdf,
            dataset=lake_dataset,
            as_of=gdf["as_of"].iloc[0],
            partition_by=[col for col in ("country", "region") if col in gdf.columns],
            dataset_type="boundaries",
        )

    logger.info("openaddresses_loaded", extra={"records": len(gdf), "run_id": run_id})
    return gdf


def load_microsoft_buildings(
    *,
    country_code: str,
    session: Optional[requests.Session] = None,
    base_url: str = MICROSOFT_BUILDINGS_URL,
    lake: Optional[DataLake] = None,
    dataset: str = "microsoft_buildings",
    cache: Optional[Cache] = None,
    rate_limiter: Optional[RateLimiter] = None,
    as_of: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """Download Microsoft global building footprints for a country."""

    session = session or _default_session()
    cache = _resolve_cache(cache)
    limiter = _ensure_rate_limiter(
        rate_limiter,
        f"microsoft_buildings:{country_code.lower()}",
        requests_per_minute=30,
        burst_size=5,
    )

    url = base_url.format(country=country_code.upper())
    limiter._wait_for_token()
    response = cache.fetch(url, etl_key=f"microsoft_buildings/{country_code.lower()}", ttl="180d", headers=session.headers)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        geojson_name = next(
            name for name in zf.namelist() if name.endswith(".geojson") or name.endswith(".json")
        )
        with zf.open(geojson_name) as handle:
            geojson = json.load(handle)

    features: Iterable[Mapping[str, object]] = geojson.get("features", [])
    gdf = gpd.GeoDataFrame.from_features(features, crs=DEFAULT_GEOMETRY_CRS)
    gdf["country_code"] = country_code.upper()
    gdf["source_id"] = "microsoft_buildings"
    gdf["ingested_at"] = datetime.now(UTC)
    gdf["as_of"] = _current_as_of(as_of)

    if "geometry" not in gdf:
        raise ValueError("Microsoft building footprints payload missing geometry column")

    gdf = gdf.drop_duplicates(subset=["geometry", "country_code"])

    _run_boundary_validations(gdf, "microsoft_buildings")

    if lake is not None and not gdf.empty:
        lake.write(
            gdf,
            dataset=dataset,
            as_of=gdf["as_of"].iloc[0],
            partition_by=["country_code"],
            dataset_type="boundaries",
        )

    logger.info(
        "microsoft_buildings_loaded", extra={"records": len(gdf), "country": country_code.upper()}
    )
    return gdf


def refresh_boundary_sources(
    *,
    lake: Optional[DataLake] = None,
    cache: Optional[Cache] = None,
    state_fips: Sequence[str] = (),
    openaddresses_runs: Sequence[tuple[str, str]] = (),
    building_countries: Sequence[str] = ("US",),
    as_of: Optional[str] = None,
) -> Dict[str, int]:
    """Orchestrate ingestion for all configured boundary datasets.

    Returns a summary dictionary mapping dataset names to record counts.
    """

    cache = _resolve_cache(cache)
    summary: Dict[str, int] = {}

    tigerweb_frames = load_tigerweb(
        state_fips=state_fips if state_fips else None,
        cache=cache,
        lake=lake,
        as_of=as_of,
    )
    for layer, frame in tigerweb_frames.items():
        summary[f"tigerweb_{layer}"] = len(frame)

    for run_id, dataset in openaddresses_runs:
        frame = load_openaddresses(
            run_id=run_id,
            dataset=dataset,
            cache=cache,
            lake=lake,
            as_of=as_of,
        )
        summary[f"openaddresses_{dataset}"] = len(frame)

    for country in building_countries:
        frame = load_microsoft_buildings(
            country_code=country,
            cache=cache,
            lake=lake,
            as_of=as_of,
        )
        summary[f"microsoft_buildings_{country.upper()}"] = len(frame)

    return summary


def _point_geometry_from_frame(frame: pd.DataFrame) -> gpd.GeoSeries:
    lon_col = next((col for col in ("lon", "longitude", "x") if col in frame.columns), None)
    lat_col = next((col for col in ("lat", "latitude", "y") if col in frame.columns), None)
    if lon_col and lat_col:
        return gpd.GeoSeries(
            [Point(xy) if pd.notna(xy[0]) and pd.notna(xy[1]) else None for xy in zip(frame[lon_col], frame[lat_col])],
            crs=DEFAULT_GEOMETRY_CRS,
        )
    raise ValueError("OpenAddresses frame missing lon/lat columns for geometry creation")


def _run_boundary_validations(gdf: gpd.GeoDataFrame, dataset: str) -> None:
    """Run geometry and CRS validations, logging warnings rather than raising."""

    if gdf.empty:
        logger.warning("boundary_validation_skipped", extra={"dataset": dataset, "reason": "empty"})
        return

    try:
        geom_result = validate_geometry(gdf)
        if geom_result.invalid_geometries:
            logger.warning(
                "boundary_geometry_issues",
                extra={
                    "dataset": dataset,
                    "invalid_geometries": geom_result.invalid_geometries,
                    "issues": geom_result.to_dict().get("validation_errors", [])[:5],
                },
            )

        crs_result = validate_crs(gdf)
        if not crs_result.get("has_crs", False) or crs_result.get("crs_name") != DEFAULT_GEOMETRY_CRS:
            logger.warning(
                "boundary_crs_mismatch",
                extra={"dataset": dataset, "crs": crs_result.get("crs_name")},
            )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("boundary_validation_failed", extra={"dataset": dataset, "error": str(exc)})


__all__ = [
    "TigerwebLayerConfig",
    "TIGERWEB_LAYERS",
    "load_tigerweb_layer",
    "load_tigerweb",
    "load_openaddresses",
    "load_microsoft_buildings",
    "refresh_boundary_sources",
]
