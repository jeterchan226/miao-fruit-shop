"""add idempotency_key to orders

Revision ID: e4c7a2d19b36
Revises: d3a91c7e5f20
Create Date: 2026-10-30 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4c7a2d19b36'
down_revision: Union[str, Sequence[str], None] = 'd3a91c7e5f20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("orders", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.create_unique_constraint(
        "orders_idempotency_key_key", "orders", ["idempotency_key"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("orders_idempotency_key_key", "orders", type_="unique")
    op.drop_column("orders", "idempotency_key")
