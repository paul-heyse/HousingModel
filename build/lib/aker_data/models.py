from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .types import GeoType


class Markets(Base):
    __tablename__ = "markets"

    msa_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    geo: Mapped[Optional[str]] = mapped_column(GeoType("MULTIPOLYGON", 4326))
    pop: Mapped[Optional[int]] = mapped_column(Integer)
    households: Mapped[Optional[int]] = mapped_column(Integer)
    data_vintage: Mapped[Optional[str]] = mapped_column(String(20))


class MarketSupply(Base):
    __tablename__ = "market_supply"

    sba_id: Mapped[str] = mapped_column(String(24), primary_key=True)
    slope_pct: Mapped[Optional[float]] = mapped_column(Float)
    protected_pct: Mapped[Optional[float]] = mapped_column(Float)
    buffer_pct: Mapped[Optional[float]] = mapped_column(Float)
    noise_overlay_pct: Mapped[Optional[float]] = mapped_column(Float)
    iz_flag: Mapped[Optional[bool]] = mapped_column()
    review_flag: Mapped[Optional[bool]] = mapped_column()
    height_idx: Mapped[Optional[float]] = mapped_column(Float)
    parking_idx: Mapped[Optional[float]] = mapped_column(Float)
    permit_per_1k: Mapped[Optional[float]] = mapped_column(Float)
    vacancy_rate: Mapped[Optional[float]] = mapped_column(Float)
    tom_days: Mapped[Optional[float]] = mapped_column(Float)
    v_intake: Mapped[Optional[str]] = mapped_column(String(20))


class MarketJobs(Base):
    __tablename__ = "market_jobs"

    sba_id: Mapped[str] = mapped_column(String(24), primary_key=True)
    tech_cagr: Mapped[Optional[float]] = mapped_column(Float)
    health_cagr: Mapped[Optional[float]] = mapped_column(Float)
    edu_cagr: Mapped[Optional[float]] = mapped_column(Float)
    mfg_cagr: Mapped[Optional[float]] = mapped_column(Float)
    tech_lq: Mapped[Optional[float]] = mapped_column(Float)
    awards_per_100k: Mapped[Optional[float]] = mapped_column(Float)
    bfs_rate: Mapped[Optional[float]] = mapped_column(Float)
    mig_25_44_per_1k: Mapped[Optional[float]] = mapped_column(Float)
    expansions_ct: Mapped[Optional[int]] = mapped_column(Integer)
    v_intake: Mapped[Optional[str]] = mapped_column(String(20))


class MarketUrban(Base):
    __tablename__ = "market_urban"

    sba_id: Mapped[str] = mapped_column(String(24), primary_key=True)
    walk_15_ct: Mapped[Optional[int]] = mapped_column(Integer)
    bike_15_ct: Mapped[Optional[int]] = mapped_column(Integer)
    k8_ct: Mapped[Optional[int]] = mapped_column(Integer)
    transit_ct: Mapped[Optional[int]] = mapped_column(Integer)
    urgent_ct: Mapped[Optional[int]] = mapped_column(Integer)
    interx_km2: Mapped[Optional[float]] = mapped_column(Float)
    bikeway_conn_idx: Mapped[Optional[float]] = mapped_column(Float)
    retail_vac: Mapped[Optional[float]] = mapped_column(Float)
    retail_rent_qoq: Mapped[Optional[float]] = mapped_column(Float)
    daytime_pop_1mi: Mapped[Optional[int]] = mapped_column(Integer)
    lastmile_flag: Mapped[Optional[bool]] = mapped_column()
    v_intake: Mapped[Optional[str]] = mapped_column(String(20))


class MarketOutdoors(Base):
    __tablename__ = "market_outdoors"

    sba_id: Mapped[str] = mapped_column(String(24), primary_key=True)
    min_trail_min: Mapped[Optional[int]] = mapped_column(Integer)
    min_ski_bus_min: Mapped[Optional[int]] = mapped_column(Integer)
    min_water_min: Mapped[Optional[int]] = mapped_column(Integer)
    park_min: Mapped[Optional[int]] = mapped_column(Integer)
    trail_mi_pc: Mapped[Optional[float]] = mapped_column(Float)
    public_land_30min_pct: Mapped[Optional[float]] = mapped_column(Float)
    pm25_var: Mapped[Optional[float]] = mapped_column(Float)
    smoke_days: Mapped[Optional[int]] = mapped_column(Integer)
    hw_rail_prox_idx: Mapped[Optional[float]] = mapped_column(Float)
    v_intake: Mapped[Optional[str]] = mapped_column(String(20))


class PillarScores(Base):
    __tablename__ = "pillar_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msa_id: Mapped[str] = mapped_column(String(12), index=True)
    supply_0_5: Mapped[Optional[float]] = mapped_column(Float)
    jobs_0_5: Mapped[Optional[float]] = mapped_column(Float)
    urban_0_5: Mapped[Optional[float]] = mapped_column(Float)
    outdoor_0_5: Mapped[Optional[float]] = mapped_column(Float)
    weighted_0_5: Mapped[Optional[float]] = mapped_column(Float)
    risk_multiplier: Mapped[Optional[float]] = mapped_column(Float)
    run_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)


class Assets(Base):
    __tablename__ = "assets"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    msa_id: Mapped[str] = mapped_column(String(12), index=True)
    geo: Mapped[Optional[str]] = mapped_column(GeoType("POINT", 4326))
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    units: Mapped[Optional[int]] = mapped_column(Integer)
    product_type: Mapped[Optional[str]] = mapped_column(String(40))


class Runs(Base):
    __tablename__ = "runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    git_sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    output_hash: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")


class Lineage(Base):
    __tablename__ = "lineage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("runs.run_id"), index=True, nullable=False
    )
    table: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hash: Mapped[str] = mapped_column(String(64))
