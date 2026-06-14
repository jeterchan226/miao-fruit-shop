from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import order_repo, product_repo, spec_repo


def _make_order(order_no: str) -> Order:
    return Order(
        order_no=order_no, status="pending_payment",
        customer_name="A", customer_phone="0912345678", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="linepay", note=None,
        subtotal=1880, shipping_fee=150, cod_fee=0, total=2030,
    )


async def test_add_and_get_by_order_no(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ABC234"))
    await db_session.flush()
    fetched = await order_repo.get_by_order_no(db_session, "MM-ABC234")
    assert fetched is not None
    assert fetched.total == 2030


async def test_get_by_order_no_missing_returns_none(db_session: AsyncSession):
    assert await order_repo.get_by_order_no(db_session, "MM-NOPE99") is None


async def test_spec_get_for_update_returns_spec(db_session: AsyncSession):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    spec_id = product.specs[0].id
    locked = await spec_repo.get_for_update(db_session, spec_id)
    assert locked is not None
    assert locked.id == spec_id
    assert locked.product.name == "甘露梨"


async def test_spec_get_for_update_missing_returns_none(db_session: AsyncSession):
    assert await spec_repo.get_for_update(db_session, 999999) is None
