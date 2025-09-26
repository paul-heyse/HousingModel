from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AssetFit(Base):
    __tablename__ = "asset_fit"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(40))
    vintage_ok: Mapped[Optional[bool]] = mapped_column()
    unit_mix_fit: Mapped[Optional[float]] = mapped_column(Float)
    parking_fit: Mapped[Optional[float]] = mapped_column(Float)
    outdoor_enablers_ct: Mapped[Optional[int]] = mapped_column(Integer)
    ev_ready_flag: Mapped[Optional[bool]] = mapped_column()
    adaptive_reuse_feasible_flag: Mapped[Optional[bool]] = mapped_column()
    fit_score: Mapped[Optional[float]] = mapped_column(Float)


class DealArchetype(Base):
    __tablename__ = "deal_archetype"

    scope_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80))
    cost: Mapped[Optional[float]] = mapped_column(Float)
    lift: Mapped[Optional[float]] = mapped_column(Float)
    payback_mo: Mapped[Optional[int]] = mapped_column(Integer)
    downtime_wk: Mapped[Optional[int]] = mapped_column(Integer)
    retention_bps: Mapped[Optional[int]] = mapped_column(Integer)
    retail_underwrite_mode: Mapped[Optional[str]] = mapped_column(String(30))


class AmenityProgram(Base):
    __tablename__ = "amenity_program"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amenity: Mapped[str] = mapped_column(String(60))
    capex: Mapped[Optional[float]] = mapped_column(Float)
    kpi_links: Mapped[Optional[str]] = mapped_column(String(120))
    modeled_impact: Mapped[Optional[str]] = mapped_column(String(120))


class RiskProfile(Base):
    __tablename__ = "risk_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    peril: Mapped[str] = mapped_column(String(40))
    severity_idx: Mapped[Optional[float]] = mapped_column(Float)
    insurance_deductible: Mapped[Optional[float]] = mapped_column(Float)
    multiplier: Mapped[Optional[float]] = mapped_column(Float)


class OpsModel(Base):
    __tablename__ = "ops_model"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nps: Mapped[Optional[int]] = mapped_column(Integer)
    reputation_idx: Mapped[Optional[float]] = mapped_column(Float)
    concession_days_saved: Mapped[Optional[int]] = mapped_column(Integer)
    cadence_plan: Mapped[Optional[str]] = mapped_column(String(120))
