"""add is_two_pack to order_items

Revision ID: d3a91c7e5f20
Revises: b7e2d4f8a9c1
Create Date: 2026-10-30 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3a91c7e5f20'
down_revision: Union[str, Sequence[str], None] = 'b7e2d4f8a9c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "order_items",
        sa.Column("is_two_pack", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # 依規格回填(含已下架);查無規格者維持 server default,視為箱裝
    op.execute(
        """
        UPDATE order_items
        SET is_two_pack = product_specs.is_two_pack
        FROM product_specs
        WHERE order_items.spec_id = product_specs.id
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("order_items", "is_two_pack")
