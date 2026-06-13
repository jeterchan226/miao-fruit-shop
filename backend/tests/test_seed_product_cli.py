import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import seed_product
from app.repositories import product_repo


async def test_seed_product_creates_product_and_specs(db_session: AsyncSession):
    product = await seed_product(db_session)
    assert product.slug == "kanro"
    fetched = await product_repo.get_by_slug(db_session, "kanro")
    assert fetched is not None
    assert len(fetched.specs) == 3
    labels = [s.label for s in fetched.specs]
    assert labels == ["2 粒精緻禮盒", "5 台斤家庭箱", "10 台斤大箱"]


async def test_seed_product_duplicate_raises(db_session: AsyncSession):
    await seed_product(db_session)
    with pytest.raises(ValueError, match="已存在"):
        await seed_product(db_session)
