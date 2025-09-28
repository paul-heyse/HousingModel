"""extra tables for asset fit, archetype, amenity, risk, ops

Revision ID: 0002_extra_tables
Revises: 0001_initial
Create Date: 2025-09-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_extra_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asset_fit",
        sa.Column("asset_id", sa.Integer(), primary_key=True),
        sa.Column("product_type", sa.String(length=40)),
        sa.Column("vintage_ok", sa.Boolean()),
        sa.Column("unit_mix_fit", sa.Float()),
        sa.Column("parking_fit", sa.Float()),
        sa.Column("outdoor_enablers_ct", sa.Integer()),
        sa.Column("ev_ready_flag", sa.Boolean()),
        sa.Column("adaptive_reuse_feasible_flag", sa.Boolean()),
        sa.Column("fit_score", sa.Float()),
    )

    op.create_table(
        "deal_archetype",
        sa.Column("scope_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("cost", sa.Float()),
        sa.Column("lift", sa.Float()),
        sa.Column("payback_mo", sa.Integer()),
        sa.Column("downtime_wk", sa.Integer()),
        sa.Column("retention_bps", sa.Integer()),
        sa.Column("retail_underwrite_mode", sa.String(length=30)),
    )

    op.create_table(
        "amenity_program",
        sa.Column("asset_id", sa.Integer(), primary_key=True),
        sa.Column("amenity", sa.String(length=60), nullable=False),
        sa.Column("capex", sa.Float()),
        sa.Column("kpi_links", sa.String(length=120)),
        sa.Column("modeled_impact", sa.String(length=120)),
    )

    op.create_table(
        "risk_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("peril", sa.String(length=40), nullable=False),
        sa.Column("severity_idx", sa.Float()),
        sa.Column("insurance_deductible", sa.Float()),
        sa.Column("multiplier", sa.Float()),
    )

    op.create_table(
        "ops_model",
        sa.Column("asset_id", sa.Integer(), primary_key=True),
        sa.Column("nps", sa.Integer()),
        sa.Column("reputation_idx", sa.Float()),
        sa.Column("concession_days_saved", sa.Integer()),
        sa.Column("cadence_plan", sa.String(length=120)),
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS ops_model"))
    op.execute(sa.text("DROP TABLE IF EXISTS risk_profile"))
    op.execute(sa.text("DROP TABLE IF EXISTS amenity_program"))
    op.execute(sa.text("DROP TABLE IF EXISTS deal_archetype"))
    op.execute(sa.text("DROP TABLE IF EXISTS asset_fit"))
