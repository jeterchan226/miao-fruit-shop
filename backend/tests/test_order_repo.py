from datetime import date, timedelta

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


async def test_list_filtered_no_filter_returns_all(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-LF01"))
    await order_repo.add(db_session, _make_order("MM-LF02"))
    await db_session.flush()
    total, orders = await order_repo.list_filtered(db_session, page=1, page_size=20)
    assert total >= 2
    nos = {o.order_no for o in orders}
    assert {"MM-LF01", "MM-LF02"} <= nos


async def test_list_filtered_by_status(db_session: AsyncSession):
    # _make_order 預設 status="pending_payment"
    await order_repo.add(db_session, _make_order("MM-ST01"))
    pending = Order(
        order_no="MM-ST02", status="pending",
        customer_name="B", customer_phone="0911000000", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="cod", note=None,
        subtotal=880, shipping_fee=0, cod_fee=30, total=910,
    )
    await order_repo.add(db_session, pending)
    await db_session.flush()
    total, results = await order_repo.list_filtered(
        db_session, status="pending", page=1, page_size=20
    )
    nos = {o.order_no for o in results}
    assert "MM-ST02" in nos
    assert "MM-ST01" not in nos
    assert all(o.status == "pending" for o in results)


async def test_list_filtered_by_q_customer_name(db_session: AsyncSession):
    named = Order(
        order_no="MM-Q01", status="pending",
        customer_name="林美麗", customer_phone="0933333333", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="cod", note=None,
        subtotal=880, shipping_fee=0, cod_fee=30, total=910,
    )
    await order_repo.add(db_session, named)
    await db_session.flush()
    _, results = await order_repo.list_filtered(db_session, q="林美麗", page=1, page_size=20)
    assert any(o.order_no == "MM-Q01" for o in results)


async def test_list_filtered_by_order_no(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-EXACT1"))
    await order_repo.add(db_session, _make_order("MM-EXACT2"))
    await db_session.flush()
    total, results = await order_repo.list_filtered(
        db_session, order_no="MM-EXACT1", page=1, page_size=20
    )
    assert total == 1
    assert results[0].order_no == "MM-EXACT1"


async def test_list_filtered_by_date(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    today = date.today()
    _, results = await order_repo.list_filtered(db_session, date_from=today, page=1, page_size=20)
    assert any(o.order_no == "MM-DT01" for o in results)
    yesterday = today - timedelta(days=1)
    _, old_results = await order_repo.list_filtered(
        db_session, date_to=yesterday, page=1, page_size=20
    )
    assert not any(o.order_no == "MM-DT01" for o in old_results)


async def test_list_filtered_pagination(db_session: AsyncSession):
    for i in range(3):
        await order_repo.add(db_session, _make_order(f"MM-PG{i:02d}"))
    await db_session.flush()
    total, page1 = await order_repo.list_filtered(db_session, page=1, page_size=2)
    assert total >= 3
    assert len(page1) == 2
    _, page2 = await order_repo.list_filtered(db_session, page=2, page_size=2)
    assert len(page2) >= 1
    assert {o.order_no for o in page1}.isdisjoint({o.order_no for o in page2})
