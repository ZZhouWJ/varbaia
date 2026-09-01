"""add transcript segments

Revision ID: 20260901_0008
Revises: 20260901_0007
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0008"
down_revision = "20260901_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("import_job_id", sa.Uuid(), sa.ForeignKey("import_jobs.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("translation", sa.Text(), nullable=True),
        sa.UniqueConstraint("import_job_id", "position", name="uq_transcript_position"),
    )
    op.create_index("ix_transcript_segments_import_job_id", "transcript_segments", ["import_job_id"])


def downgrade() -> None:
    op.drop_table("transcript_segments")
