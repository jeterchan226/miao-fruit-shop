"""add line fields to orders

Revision ID: 6f74f5a8f3db
Revises: 872ffc62f4fd
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f74f5a8f3db"
down_revision: Union[str, Sequence[str], None] = "872ffc62f4fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("orders", sa.Column("line_user_id", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("line_display_name", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("line_picture_url", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("line_friendship_status", sa.String(), nullable=True))
    op.add_column(
        "orders",
        sa.Column(
            "line_notification_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(op.f("ix_orders_line_user_id"), "orders", ["line_user_id"], unique=False)
    op.alter_column("orders", "line_notification_consent", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_orders_line_user_id"), table_name="orders")
    op.drop_column("orders", "line_notification_consent")
    op.drop_column("orders", "line_friendship_status")
    op.drop_column("orders", "line_picture_url")
    op.drop_column("orders", "line_display_name")
    op.drop_column("orders", "line_user_id")
