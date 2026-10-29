"""add source to orders

Revision ID: b7e2d4f8a9c1
Revises: a3f5c9d2b1e4
Create Date: 2026-10-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e2d4f8a9c1"
down_revision: Union[str, Sequence[str], None] = "a3f5c9d2b1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 只新增帶預設值欄位:既有訂單皆為 storefront,舊版後端不寫此欄也不受影響
    op.add_column(
        "orders",
        sa.Column("source", sa.String(), nullable=False, server_default="storefront"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "source")
