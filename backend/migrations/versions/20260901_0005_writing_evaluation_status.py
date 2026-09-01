"""add writing evaluation status

Revision ID: 20260901_0005
Revises: 20260901_0004
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0005"
down_revision = "20260901_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "writing_attempts",
        sa.Column("evaluation_status", sa.String(length=24), nullable=False, server_default="queued"),
    )
    op.add_column("writing_attempts", sa.Column("evaluation_error", sa.String(length=500), nullable=True))
    op.create_index("ix_writing_attempts_evaluation_status", "writing_attempts", ["evaluation_status"])
    op.alter_column("writing_attempts", "evaluation_status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_writing_attempts_evaluation_status", table_name="writing_attempts")
    op.drop_column("writing_attempts", "evaluation_error")
    op.drop_column("writing_attempts", "evaluation_status")
