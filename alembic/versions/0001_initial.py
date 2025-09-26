"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-09-26
"""

from __future__ import annotations

import sqlalchemy as sa
from geoalchemy2 import Geometry

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    def geom(type_name: str, srid: int):
        if dialect == "postgresql":
            return Geometry(geometry_type=type_name, srid=srid)
        # Fallback for SQLite (no SpatiaLite in CI)
        return sa.Text()

    op.create_table(
        "markets",
        sa.Column("msa_id", sa.String(length=12), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("geo", geom("MULTIPOLYGON", 4326)),
        sa.Column("pop", sa.Integer()),
        sa.Column("households", sa.Integer()),
        sa.Column("data_vintage", sa.String(length=20)),
    )

    op.create_table(
        "pillar_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("msa_id", sa.String(length=12), index=True),
        sa.Column("supply_0_5", sa.Float()),
        sa.Column("jobs_0_5", sa.Float()),
        sa.Column("urban_0_5", sa.Float()),
        sa.Column("outdoor_0_5", sa.Float()),
        sa.Column("weighted_0_5", sa.Float()),
        sa.Column("risk_multiplier", sa.Float()),
        sa.Column("run_id", sa.Integer()),
    )

    op.create_table(
        "assets",
        sa.Column("asset_id", sa.Integer(), primary_key=True),
        sa.Column("msa_id", sa.String(length=12), index=True),
        sa.Column("geo", geom("POINT", 4326)),
        sa.Column("year_built", sa.Integer()),
        sa.Column("units", sa.Integer()),
        sa.Column("product_type", sa.String(length=40)),
    )

    op.create_table(
        "runs",
        sa.Column("run_id", sa.Integer(), primary_key=True),
        sa.Column("git_sha", sa.String(length=40)),
        sa.Column("config_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "lineage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table", sa.String(length=64), index=True),
        sa.Column("source", sa.String(length=64)),
        sa.Column("source_url", sa.Text()),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
        sa.Column("hash", sa.String(length=64)),
    )


def downgrade() -> None:
    op.drop_table("lineage")
    op.drop_table("runs")
    op.drop_table("assets")
    op.drop_table("pillar_scores")
    op.drop_table("markets")
