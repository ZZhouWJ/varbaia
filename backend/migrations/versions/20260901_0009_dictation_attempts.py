"""add dictation attempts

Revision ID: 20260901_0009
Revises: 20260901_0008
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0009"
down_revision = "20260901_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dictation_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), sa.ForeignKey("import_jobs.id")),
        sa.Column("segment_id", sa.Uuid(), sa.ForeignKey("transcript_segments.id")),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("reference", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("missed_words_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dictation_attempts_owner_user_id", "dictation_attempts", ["owner_user_id"])


def downgrade() -> None:
    op.drop_table("dictation_attempts")
