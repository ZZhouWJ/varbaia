"""add owned media assets

Revision ID: 20260901_0007
Revises: 20260901_0006
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0007"
down_revision = "20260901_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), sa.ForeignKey("import_jobs.id"), nullable=False),
        sa.Column("stored_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_assets_owner_user_id", "media_assets", ["owner_user_id"])
    op.create_index("ix_media_assets_import_job_id", "media_assets", ["import_job_id"])


def downgrade() -> None:
    op.drop_table("media_assets")
