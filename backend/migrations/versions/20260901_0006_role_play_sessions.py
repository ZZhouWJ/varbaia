"""add role play sessions

Revision ID: 20260901_0006
Revises: 20260901_0005
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260901_0006"
down_revision = "20260901_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_play_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scenario", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_role_play_sessions_owner_user_id", "role_play_sessions", ["owner_user_id"])
    op.create_table(
        "role_play_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.Uuid(), sa.ForeignKey("role_play_sessions.id"), nullable=False),
        sa.Column("speaker", sa.String(length=24), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("coaching_tip", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_role_play_messages_session_id", "role_play_messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("role_play_messages")
    op.drop_table("role_play_sessions")
