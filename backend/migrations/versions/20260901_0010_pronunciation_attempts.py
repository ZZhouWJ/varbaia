"""add pronunciation attempts

Revision ID: 20260901_0010
Revises: 20260901_0009
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0010"
down_revision = "20260901_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pronunciation_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reference_text", sa.Text(), nullable=False),
        sa.Column("stored_name", sa.String(120), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("evaluation_status", sa.String(24), nullable=False),
        sa.Column("result_json", sa.Text()),
        sa.Column("evaluation_error", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pronunciation_attempts_owner_user_id", "pronunciation_attempts", ["owner_user_id"])
    op.create_index("ix_pronunciation_attempts_evaluation_status", "pronunciation_attempts", ["evaluation_status"])


def downgrade() -> None:
    op.drop_table("pronunciation_attempts")
