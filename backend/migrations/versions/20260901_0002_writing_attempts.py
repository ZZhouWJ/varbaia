"""writing attempt persistence

Revision ID: 20260901_0002
Revises: 20260831_0001
Create Date: 2026-09-01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260901_0002"
down_revision = "20260831_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "writing_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("draft", sa.Text(), nullable=False),
        sa.Column("clarity_score", sa.Integer()),
        sa.Column("feedback_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_writing_attempts_owner_user_id", "writing_attempts", ["owner_user_id"])


def downgrade() -> None:
    op.drop_table("writing_attempts")
