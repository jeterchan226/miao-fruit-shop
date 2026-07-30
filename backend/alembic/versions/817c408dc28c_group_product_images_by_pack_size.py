"""group product images by pack size

Revision ID: 817c408dc28c
Revises: ccae80d8b67e
Create Date: 2026-07-30 19:05:31.718621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '817c408dc28c'
down_revision: Union[str, Sequence[str], None] = 'ccae80d8b67e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('product_images', sa.Column('is_two_pack', sa.Boolean(), nullable=True))
    op.execute(
        """
        UPDATE product_images
        SET is_two_pack = product_specs.is_two_pack
        FROM product_specs
        WHERE product_images.spec_id = product_specs.id
        """
    )
    op.drop_constraint('product_images_spec_id_fkey', 'product_images', type_='foreignkey')
    op.drop_index('ix_product_images_spec_id', table_name='product_images')
    op.drop_column('product_images', 'spec_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('product_images', sa.Column('spec_id', sa.Integer(), nullable=True))
    op.create_index(
        'ix_product_images_spec_id', 'product_images', ['spec_id'], unique=False
    )
    op.create_foreign_key(
        'product_images_spec_id_fkey', 'product_images', 'product_specs', ['spec_id'], ['id']
    )
    op.drop_column('product_images', 'is_two_pack')
