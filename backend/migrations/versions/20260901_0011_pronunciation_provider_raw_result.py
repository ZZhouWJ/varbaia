"""store raw pronunciation provider diagnostics separately

Revision ID: 20260901_0011
Revises: 20260901_0010
"""

from alembic import op
import sqlalchemy as sa

revision = "20260901_0011"
down_revision = "20260901_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pronunciation_attempts", sa.Column("raw_provider_result_json", sa.Text()))


def downgrade() -> None:
    op.drop_column("pronunciation_attempts", "raw_provider_result_json")
