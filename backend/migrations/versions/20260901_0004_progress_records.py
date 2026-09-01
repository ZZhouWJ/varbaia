"""add owner learning progress records

Revision ID: 20260901_0004
Revises: 20260901_0003
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0004"
down_revision = "20260901_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "progress_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("completion_percent", sa.Integer(), nullable=False),
        sa.Column("last_position_seconds", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_user_id", "resource_type", "resource_id", name="uq_progress_resource"
        ),
    )
    op.create_index("ix_progress_records_owner_user_id", "progress_records", ["owner_user_id"])
    op.create_index("ix_progress_records_resource_id", "progress_records", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_progress_records_resource_id", table_name="progress_records")
    op.drop_index("ix_progress_records_owner_user_id", table_name="progress_records")
    op.drop_table("progress_records")
