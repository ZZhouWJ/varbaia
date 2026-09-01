"""store role play synthesized audio

Revision ID: 20260901_0012
Revises: 20260901_0011
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0012"
down_revision = "20260901_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("role_play_messages", sa.Column("audio_stored_name", sa.String(120), unique=True))
    op.add_column("role_play_messages", sa.Column("audio_mime_type", sa.String(100)))


def downgrade() -> None:
    op.drop_column("role_play_messages", "audio_mime_type")
    op.drop_column("role_play_messages", "audio_stored_name")
