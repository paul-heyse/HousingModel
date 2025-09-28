"""ops_model table

Revision ID: 0008_ops_model
Revises: 0007_asset_fit
Create Date: 2025-09-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_ops_model"
down_revision = "0007_asset_fit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ops_model",
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.asset_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nps", sa.Integer(), nullable=True),
        sa.Column("reputation_idx", sa.Float(), nullable=True),
        sa.Column("max_discount_pct", sa.Float(), nullable=True),
        sa.Column("max_concession_days", sa.Integer(), nullable=True),
        sa.Column("concession_days_saved", sa.Integer(), nullable=True),
        sa.Column("cadence_plan", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ops_model")


