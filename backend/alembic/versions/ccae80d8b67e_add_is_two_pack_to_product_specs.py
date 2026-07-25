"""add is_two_pack to product_specs

Revision ID: ccae80d8b67e
Revises: 6f74f5a8f3db
Create Date: 2026-07-25 13:48:15.032010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccae80d8b67e'
down_revision: Union[str, Sequence[str], None] = '6f74f5a8f3db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "product_specs",
        sa.Column("is_two_pack", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("product_specs", "is_two_pack")
