"""seed user groups

Revision ID: 74fea5cb3a32
Revises: 19da0d7c2e67
Create Date: 2026-02-05 11:12:57.502475

"""

from typing import Sequence, Union
from sqlalchemy.sql import table, column
from sqlalchemy import String
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "74fea5cb3a32"
down_revision: Union[str, Sequence[str], None] = "19da0d7c2e67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user_groups = table(
        "user_groups",
        column("name", String),
    )

    op.bulk_insert(
        user_groups,
        [
            {"name": "USER"},
            {"name": "MODERATOR"},
            {"name": "ADMIN"},
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM user_groups WHERE name IN ('USER', 'MODERATOR', 'ADMIN')")
