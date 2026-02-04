"""Initial

Revision ID: 0186a23db577
Revises:
Create Date: 2026-02-04 15:06:49.883388

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0186a23db577"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
