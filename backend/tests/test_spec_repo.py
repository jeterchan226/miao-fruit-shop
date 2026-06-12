from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo, spec_repo


async def test_add_and_get_spec(db_session: AsyncSession):
    product = await product_repo.add(
        db_session,
        Product(slug="kanro", name="甘露梨", description="d", image="i", season="s"),
    )
    spec = await spec_repo.add(
        db_session,
        ProductSpec(
            product_id=product.id, label="5 台斤", qty_text="q", price=1880,
            stock_qty=10,
        ),
    )
    assert spec.id is not None
    fetched = await spec_repo.get_by_id(db_session, spec.id)
    assert fetched is not None and fetched.label == "5 台斤"


async def test_get_spec_missing_returns_none(db_session: AsyncSession):
    assert await spec_repo.get_by_id(db_session, 999999) is None
