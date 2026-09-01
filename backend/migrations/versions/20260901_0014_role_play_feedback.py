"""store role play completion feedback

Revision ID: 20260901_0014
Revises: 20260901_0013
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0014"
down_revision = "20260901_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("role_play_sessions", sa.Column("feedback_json", sa.Text()))


def downgrade() -> None:
    op.drop_column("role_play_sessions", "feedback_json")
