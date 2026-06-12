import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo
from app.schemas.product import ProductUpdate, SpecCreate, SpecUpdate
from app.services import product_service


async def _seed(session, *, product_active=True):
    product = Product(
        slug="kanro", name="甘露梨", description="d", image="i", season="s",
        is_active=product_active,
    )
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, sort_order=1),
        ProductSpec(label="B", qty_text="q", price=1880, stock_qty=3,
                    low_stock_threshold=3, sort_order=2),
        ProductSpec(label="C", qty_text="q", price=3580, stock_qty=0, sort_order=3,
                    is_active=False),
    ]
    return await product_repo.add(session, product)


async def test_list_public_only_active_with_status(db_session: AsyncSession):
    await _seed(db_session)
    products = await product_service.list_public_products(db_session)
    assert len(products) == 1
    specs = products[0].specs
    assert [s.label for s in specs] == ["A", "B"]
    assert specs[0].stock_status == "in"
    assert specs[1].stock_status == "low"


async def test_list_public_excludes_inactive_product(db_session: AsyncSession):
    await _seed(db_session, product_active=False)
    assert await product_service.list_public_products(db_session) == []


async def test_list_admin_includes_inactive_and_stock_qty(db_session: AsyncSession):
    await _seed(db_session)
    products = await product_service.list_admin_products(db_session)
    specs = products[0].specs
    assert [s.label for s in specs] == ["A", "B", "C"]
    assert specs[0].stock_qty == 20


async def test_update_product_changes_fields(db_session: AsyncSession):
    p = await _seed(db_session)
    updated = await product_service.update_product(
        db_session, p.id, ProductUpdate(name="新名字")
    )
    assert updated.name == "新名字"
    assert updated.description == "d"  # 未傳入的欄位不應被覆蓋(exclude_unset)


async def test_update_product_missing_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await product_service.update_product(db_session, 999999, ProductUpdate(name="x"))


async def test_create_update_softdelete_spec(db_session: AsyncSession):
    p = await _seed(db_session)
    created = await product_service.create_spec(
        db_session, p.id,
        SpecCreate(label="D", qty_text="q", price=500, stock_qty=2, sort_order=4),
    )
    assert created.stock_status == "low"
    updated = await product_service.update_spec(
        db_session, created.id, SpecUpdate(price=600)
    )
    assert updated.price == 600
    await product_service.soft_delete_spec(db_session, created.id)
    products = await product_service.list_public_products(db_session)
    assert "D" not in [s.label for s in products[0].specs]


async def test_spec_ops_missing_raise(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await product_service.update_spec(db_session, 999999, SpecUpdate(price=1))
    with pytest.raises(NotFoundError):
        await product_service.soft_delete_spec(db_session, 999999)
