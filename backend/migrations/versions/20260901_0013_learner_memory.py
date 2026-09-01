"""add learner memory items

Revision ID: 20260901_0013
Revises: 20260901_0012
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0013"
down_revision = "20260901_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_memory_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", sa.String(24), nullable=False),
        sa.Column("memory_key", sa.String(160), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_user_id", "category", "memory_key", name="uq_memory_owner_key"),
    )
    op.create_index("ix_learner_memory_items_owner_user_id", "learner_memory_items", ["owner_user_id"])
    op.create_index("ix_learner_memory_items_category", "learner_memory_items", ["category"])
    op.create_index("ix_learner_memory_items_status", "learner_memory_items", ["status"])


def downgrade() -> None:
    op.drop_table("learner_memory_items")
