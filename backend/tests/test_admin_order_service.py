from datetime import date as date_type

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStatusTransition, NotFoundError
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import order_repo
from app.services import admin_order_service


def _make_order(
    order_no: str,
    *,
    status: str = "pending",
    customer_name: str = "王小明",
    customer_phone: str = "0912345678",
) -> Order:
    return Order(
        order_no=order_no,
        status=status,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=None,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date_type(2026, 10, 1),
        delivery_window="any",
        payment_method="cod",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=30,
        total=910,
    )


async def test_list_orders_empty(db_session: AsyncSession):
    resp = await admin_order_service.list_orders(db_session)
    assert resp.total == 0
    assert resp.items == []
    assert resp.page == 1
    assert resp.page_size == 20


async def test_list_orders_returns_all(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-LS01"))
    await order_repo.add(db_session, _make_order("MM-LS02"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session)
    assert resp.total == 2
    assert len(resp.items) == 2


async def test_list_orders_filter_by_status(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ST01", status="pending"))
    await order_repo.add(db_session, _make_order("MM-ST02", status="confirmed"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, status="pending")
    nos = {item.order_no for item in resp.items}
    assert "MM-ST01" in nos
    assert "MM-ST02" not in nos
    assert all(item.status == "pending" for item in resp.items)


async def test_list_orders_filter_by_q(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-Q01", customer_name="林美麗"))
    await order_repo.add(db_session, _make_order("MM-Q02", customer_name="陳大明"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, q="林美麗")
    assert resp.total == 1
    assert resp.items[0].order_no == "MM-Q01"


async def test_list_orders_pagination(db_session: AsyncSession):
    for i in range(3):
        await order_repo.add(db_session, _make_order(f"MM-PG{i:02d}"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, page=1, page_size=2)
    assert resp.total == 3
    assert len(resp.items) == 2


async def test_get_order_detail(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    detail = await admin_order_service.get_order_detail(db_session, "MM-DT01")
    assert detail.order_no == "MM-DT01"
    assert detail.ship_city == "台北市"
    assert detail.customer_name == "王小明"
    assert isinstance(detail.items, list)


async def test_get_order_detail_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.get_order_detail(db_session, "MM-GHOST")


async def test_change_status_valid_transition(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR01", status="pending"))
    await db_session.flush()
    result = await admin_order_service.change_order_status(db_session, "MM-TR01", "confirmed")
    assert result.status == "confirmed"


async def test_change_status_invalid_transition_raises(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR02", status="shipping"))
    await db_session.flush()
    with pytest.raises(InvalidStatusTransition):
        await admin_order_service.change_order_status(db_session, "MM-TR02", "cancelled")


async def test_change_status_order_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.change_order_status(db_session, "MM-GHOST", "confirmed")


async def test_cancel_restores_stock(db_session: AsyncSession):
    product = Product(
        slug="kanro2", name="甘露梨", description="d", image="i", season="s"
    )
    db_session.add(product)
    await db_session.flush()

    spec = ProductSpec(
        product_id=product.id,
        label="A",
        qty_text="q",
        price=880,
        stock_qty=5,
        sort_order=1,
    )
    db_session.add(spec)
    await db_session.flush()

    order = _make_order("MM-CANCEL1", status="confirmed")
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        spec_id=spec.id,
        product_name="甘露梨",
        spec_label="A",
        unit_price=880,
        qty=2,
        line_total=1760,
    )
    db_session.add(item)
    await db_session.flush()

    await admin_order_service.change_order_status(db_session, "MM-CANCEL1", "cancelled")
    await db_session.refresh(spec)
    assert spec.stock_qty == 7  # 5 + 2


async def test_cancel_with_null_spec_id_skips_silently(db_session: AsyncSession):
    order = _make_order("MM-CANCEL2", status="confirmed")
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=99999,
        spec_id=None,
        product_name="已下架商品",
        spec_label="A",
        unit_price=880,
        qty=1,
        line_total=880,
    )
    db_session.add(item)
    await db_session.flush()

    result = await admin_order_service.change_order_status(db_session, "MM-CANCEL2", "cancelled")
    assert result.status == "cancelled"
