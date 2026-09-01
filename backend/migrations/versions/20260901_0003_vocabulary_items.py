"""vocabulary persistence

Revision ID: 20260901_0003
Revises: 20260901_0002
Create Date: 2026-09-01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260901_0003"
down_revision = "20260901_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("term", sa.String(160), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("ease", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vocabulary_items_owner_user_id", "vocabulary_items", ["owner_user_id"])


def downgrade() -> None:
    op.drop_table("vocabulary_items")
