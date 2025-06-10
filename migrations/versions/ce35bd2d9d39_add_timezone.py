"""add timezone column

Revision ID: ce35bd2d9d39
Revises: 5b221ee93923
Create Date: 2025-06-01 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'ce35bd2d9d39'
down_revision: str | None = '5b221ee93923'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'timezone')
