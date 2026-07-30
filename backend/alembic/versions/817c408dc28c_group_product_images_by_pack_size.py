"""group product images by pack size

Revision ID: 817c408dc28c
Revises: ccae80d8b67e
Create Date: 2026-07-30 19:05:31.718621

NOTE on downgrade():
`upgrade()` merges each image's per-spec association into a per-pack-size
group (`is_two_pack`), discarding the original `spec_id` values in the
process. `downgrade()` can only restore the `spec_id` *column's schema*
(type, index, FK) — it has no way to recover which spec each image
originally belonged to, since that mapping no longer exists anywhere after
`upgrade()` runs. After a downgrade, every row's `spec_id` will be NULL and
must be re-populated manually (or images re-associated) if per-spec
association is needed again.
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
    """Downgrade schema.

    This only restores the `spec_id` column's schema (type, index, FK
    constraint) with all values NULL. It does NOT and cannot restore each
    row's original spec association — that information was permanently
    discarded when `upgrade()` merged per-spec images into per-pack-size
    (`is_two_pack`) groups. See module docstring for details.
    """
    op.add_column('product_images', sa.Column('spec_id', sa.Integer(), nullable=True))
    op.create_index(
        'ix_product_images_spec_id', 'product_images', ['spec_id'], unique=False
    )
    op.create_foreign_key(
        'product_images_spec_id_fkey', 'product_images', 'product_specs', ['spec_id'], ['id']
    )
    op.drop_column('product_images', 'is_two_pack')
