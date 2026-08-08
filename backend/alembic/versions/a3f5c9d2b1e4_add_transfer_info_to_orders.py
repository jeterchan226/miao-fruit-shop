"""add transfer info to orders

Revision ID: a3f5c9d2b1e4
Revises: 817c408dc28c
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f5c9d2b1e4"
down_revision: Union[str, Sequence[str], None] = "817c408dc28c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("orders", sa.Column("transfer_last5", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("transfer_payer_name", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("transfer_note", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "transfer_note")
    op.drop_column("orders", "transfer_payer_name")
    op.drop_column("orders", "transfer_last5")
