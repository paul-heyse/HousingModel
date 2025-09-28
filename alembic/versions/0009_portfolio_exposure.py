"""Portfolio exposure monitoring tables

Revision ID: 0009
Revises: 0008_amenity_roi
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008_amenity_roi"
branch_labels = None
depends_on = None


def upgrade():
    """Create portfolio exposure monitoring tables."""

    # Portfolio positions table
    op.create_table(
        "portfolio_positions",
        sa.Column("position_id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), nullable=True, index=True),
        sa.Column("msa_id", sa.String(12), nullable=True, index=True),
        sa.Column("strategy", sa.String(50), nullable=True, index=True),
        sa.Column("state", sa.String(2), nullable=True, index=True),
        sa.Column("vintage", sa.Integer, nullable=True, index=True),
        sa.Column("construction_type", sa.String(50), nullable=True, index=True),
        sa.Column("rent_band", sa.String(20), nullable=True, index=True),
        sa.Column("position_value", sa.Float, nullable=False),
        sa.Column("units", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )

    # Portfolio exposures table
    op.create_table(
        "portfolio_exposures",
        sa.Column("exposure_id", sa.String(36), primary_key=True),
        sa.Column("dimension_type", sa.String(50), nullable=False, index=True),
        sa.Column("dimension_value", sa.String(100), nullable=False, index=True),
        sa.Column("exposure_pct", sa.Float, nullable=False),
        sa.Column("exposure_value", sa.Float, nullable=False),
        sa.Column("total_portfolio_value", sa.Float, nullable=False),
        sa.Column("as_of_date", sa.DateTime, nullable=False, index=True),
        sa.Column("run_id", sa.String(36), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("dimension_type", "dimension_value", "as_of_date", name="uq_exposure_dimension_date"),
    )

    # Exposure thresholds table
    op.create_table(
        "exposure_thresholds",
        sa.Column("threshold_id", sa.String(36), primary_key=True),
        sa.Column("dimension_type", sa.String(50), nullable=False, index=True),
        sa.Column("dimension_value", sa.String(100), nullable=True, index=True),
        sa.Column("threshold_pct", sa.Float, nullable=False),
        sa.Column("threshold_type", sa.String(20), nullable=False, server_default="maximum"),
        sa.Column("severity_level", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), onupdate=sa.text("CURRENT_TIMESTAMP")),
    )

    # Portfolio alerts table
    op.create_table(
        "portfolio_alerts",
        sa.Column("alert_id", sa.String(36), primary_key=True),
        sa.Column("threshold_id", sa.String(36), sa.ForeignKey("exposure_thresholds.threshold_id"), nullable=False),
        sa.Column("exposure_id", sa.String(36), sa.ForeignKey("portfolio_exposures.exposure_id"), nullable=False),
        sa.Column("breach_pct", sa.Float, nullable=False),
        sa.Column("alert_message", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("acknowledged_by", sa.String(100), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("status IN ('active', 'acknowledged', 'resolved')", name="check_alert_status"),
    )


def downgrade():
    """Drop portfolio exposure monitoring tables."""

    op.drop_table("portfolio_alerts")
    op.drop_table("exposure_thresholds")
    op.drop_table("portfolio_exposures")
    op.drop_table("portfolio_positions")
