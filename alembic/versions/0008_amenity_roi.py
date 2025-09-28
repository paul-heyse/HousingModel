"""Revise amenity_program for ROI engine

Revision ID: 0008_amenity_roi
Revises: 0007_asset_fit
Create Date: 2025-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_amenity_roi"
down_revision = "0007_asset_fit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("amenity_program")

    op.create_table(
        "amenity_program",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amenity_code", sa.String(length=40), nullable=False),
        sa.Column("amenity_name", sa.String(length=120), nullable=True),
        sa.Column("capex", sa.Float(), nullable=True),
        sa.Column("opex_monthly", sa.Float(), nullable=True),
        sa.Column("rent_premium_per_unit", sa.Float(), nullable=True),
        sa.Column("retention_delta_bps", sa.Float(), nullable=True),
        sa.Column("membership_revenue_monthly", sa.Float(), nullable=True),
        sa.Column("avg_monthly_rent", sa.Float(), nullable=True),
        sa.Column("utilization_rate", sa.Float(), nullable=True),
        sa.Column("payback_months", sa.Float(), nullable=True),
        sa.Column("noi_delta_annual", sa.Float(), nullable=True),
        sa.Column("data_vintage", sa.String(length=20), nullable=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("runs.run_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("calculation_method", sa.String(length=32), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "asset_id", "amenity_code", name="uq_amenity_program_asset_code"
        ),
    )
    op.create_index("ix_amenity_program_asset_id", "amenity_program", ["asset_id"])
    op.create_index("ix_amenity_program_amenity_code", "amenity_program", ["amenity_code"])
    op.create_index("ix_amenity_program_run_id", "amenity_program", ["run_id"])
    op.create_index("ix_amenity_program_noi_delta", "amenity_program", ["noi_delta_annual"])


def downgrade() -> None:
    op.drop_index("ix_amenity_program_noi_delta", table_name="amenity_program")
    op.drop_index("ix_amenity_program_run_id", table_name="amenity_program")
    op.drop_index("ix_amenity_program_amenity_code", table_name="amenity_program")
    op.drop_index("ix_amenity_program_asset_id", table_name="amenity_program")
    op.drop_table("amenity_program")

    op.create_table(
        "amenity_program",
        sa.Column("asset_id", sa.Integer(), primary_key=True),
        sa.Column("amenity", sa.String(length=60), nullable=False),
        sa.Column("capex", sa.Float(), nullable=True),
        sa.Column("kpi_links", sa.String(length=120), nullable=True),
        sa.Column("modeled_impact", sa.String(length=120), nullable=True),
    )
