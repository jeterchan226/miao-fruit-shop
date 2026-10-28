from datetime import date as date_type

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EvenQtyRequiredError,
    InsufficientStockError,
    InvalidStatusTransition,
    NotFoundError,
    OrderNotEditableError,
    PriceChangedError,
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import order_repo
from app.schemas.order import AdminOrderItemUpdate, AdminOrderTransferUpdate, AdminOrderUpdate
from app.services import admin_order_service, order_items


def _make_order(
    order_no: str,
    *,
    status: str = "pending_payment",
    customer_name: str = "王小明",
    customer_phone: str = "0912345678",
) -> Order:
    return Order(
        order_no=order_no,
        status=status,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=None,
        line_user_id="UADMIN123",
        line_display_name="後台測試",
        line_picture_url="https://example.com/admin-line.jpg",
        line_friendship_status="friend",
        line_notification_consent=True,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date_type(2026, 10, 1),
        delivery_window="any",
        payment_method="transfer",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=0,
        total=880,
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


async def test_list_orders_includes_item_summary(db_session: AsyncSession):
    order = _make_order("MM-IT01")
    order.items = [
        OrderItem(
            product_id=1,
            product_name="甘露梨 禮盒",
            spec_label="5 台斤",
            unit_price=2020,
            qty=1,
            line_total=2020,
        ),
        OrderItem(
            product_id=1,
            product_name="秋月梨 禮盒",
            spec_label="3 台斤",
            unit_price=2020,
            qty=1,
            line_total=2020,
        ),
    ]
    await order_repo.add(db_session, order)
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session)
    item = next(i for i in resp.items if i.order_no == "MM-IT01")
    assert item.first_item_name == "甘露梨 禮盒"
    assert item.item_count == 2


async def test_list_orders_item_summary_empty_when_no_items(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-IT00"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session)
    item = next(i for i in resp.items if i.order_no == "MM-IT00")
    assert item.first_item_name is None
    assert item.item_count == 0


async def test_list_orders_filter_by_status(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ST01", status="pending_payment"))
    await order_repo.add(db_session, _make_order("MM-ST02", status="shipping"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, status="pending_payment")
    nos = {item.order_no for item in resp.items}
    assert "MM-ST01" in nos
    assert "MM-ST02" not in nos
    assert all(item.status == "pending_payment" for item in resp.items)


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
    assert detail.line_user_id == "UADMIN123"
    assert detail.line_display_name == "後台測試"
    assert detail.line_notification_consent is True
    assert isinstance(detail.items, list)


async def test_get_order_detail_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.get_order_detail(db_session, "MM-GHOST")


async def test_change_status_valid_transition(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR01", status="pending_payment"))
    await db_session.flush()
    result = await admin_order_service.change_order_status(db_session, "MM-TR01", "ready")
    assert result.status == "ready"


async def test_change_status_invalid_transition_raises(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR02", status="shipping"))
    await db_session.flush()
    with pytest.raises(InvalidStatusTransition):
        await admin_order_service.change_order_status(db_session, "MM-TR02", "cancelled")


async def test_change_status_order_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.change_order_status(db_session, "MM-GHOST", "shipping")


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

    order = _make_order("MM-CANCEL1", status="pending_payment")
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
    order = _make_order("MM-CANCEL2", status="pending_payment")
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


async def _make_product_and_spec(
    db_session: AsyncSession,
    *,
    slug: str,
    price: int = 880,
    stock_qty: int = 5,
    is_two_pack: bool = False,
) -> ProductSpec:
    product = Product(
        slug=slug, name="甘露梨", description="d", image="i", season="s"
    )
    db_session.add(product)
    await db_session.flush()
    spec = ProductSpec(
        product_id=product.id,
        label="A",
        qty_text="q",
        price=price,
        stock_qty=stock_qty,
        sort_order=1,
        is_two_pack=is_two_pack,
    )
    db_session.add(spec)
    await db_session.flush()
    return spec


async def test_update_order_simple_fields_leaves_items_untouched(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ED01"))
    await db_session.flush()

    result = await admin_order_service.update_order(
        db_session,
        "MM-ED01",
        AdminOrderUpdate(customer_name="陳大文", note="客戶臨時改地址"),
    )
    assert result.customer_name == "陳大文"
    assert result.note == "客戶臨時改地址"
    assert result.ship_city == "台北市"
    assert result.items == []


async def test_update_order_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.update_order(
            db_session, "MM-GHOST", AdminOrderUpdate(note="x")
        )


async def test_update_order_not_editable_when_shipping(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ED02", status="shipping"))
    await db_session.flush()
    with pytest.raises(OrderNotEditableError):
        await admin_order_service.update_order(
            db_session, "MM-ED02", AdminOrderUpdate(note="不該成功")
        )


async def test_update_order_not_editable_when_cancelled(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ED03", status="cancelled"))
    await db_session.flush()
    with pytest.raises(OrderNotEditableError):
        await admin_order_service.update_order(
            db_session, "MM-ED03", AdminOrderUpdate(note="不該成功")
        )


async def _make_order_with_item(
    db_session: AsyncSession, order_no: str, spec: ProductSpec, *, unit_price: int, qty: int
) -> Order:
    order = _make_order(order_no)
    order.subtotal = unit_price * qty
    order.shipping_fee = 0
    order.total = unit_price * qty
    db_session.add(order)
    await db_session.flush()
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=spec.product_id,
            spec_id=spec.id,
            product_name="甘露梨",
            spec_label=spec.label,
            unit_price=unit_price,
            qty=qty,
            line_total=unit_price * qty,
        )
    )
    await db_session.flush()
    return order


def _total(lines: list[tuple[int, int, bool]]) -> int:
    return order_items.compute_amounts(lines).total


async def test_update_order_address_only_after_price_change_keeps_order_price(
    db_session: AsyncSession,
):
    # 回歸:規格調價後只改地址,下單價、金額、庫存都不變(ADR 0004)
    spec = await _make_product_and_spec(db_session, slug="reprice", price=880, stock_qty=5)
    await _make_order_with_item(db_session, "MM-ED04", spec, unit_price=880, qty=2)
    spec.price = 1000
    await db_session.flush()

    result = await admin_order_service.update_order(
        db_session, "MM-ED04", AdminOrderUpdate(ship_street="中山北路2號")
    )

    assert result.ship_street == "中山北路2號"
    assert result.items[0].unit_price == 880
    assert result.items[0].line_total == 1760
    assert (result.subtotal, result.shipping_fee, result.total) == (1760, 0, 1760)
    await db_session.refresh(spec)
    assert spec.stock_qty == 5


async def test_update_order_address_only_with_inactive_spec(db_session: AsyncSession):
    # 回歸:訂單含已下架規格時仍可只改地址
    spec = await _make_product_and_spec(db_session, slug="retired", price=880, stock_qty=5)
    await _make_order_with_item(db_session, "MM-ED05", spec, unit_price=880, qty=2)
    spec.is_active = False
    await db_session.flush()

    result = await admin_order_service.update_order(
        db_session, "MM-ED05", AdminOrderUpdate(ship_street="中山北路2號")
    )

    assert result.ship_street == "中山北路2號"
    assert [(i.spec_id, i.qty, i.unit_price) for i in result.items] == [(spec.id, 2, 880)]
    await db_session.refresh(spec)
    assert spec.stock_qty == 5


async def test_update_order_items_applies_diff_keeping_order_price(db_session: AsyncSession):
    # items 為期望的完整清單:既有規格加量沿用原下單價、新規格用目前價格
    kept = await _make_product_and_spec(db_session, slug="kept", price=880, stock_qty=5)
    added = await _make_product_and_spec(db_session, slug="added", price=500, stock_qty=10)
    await _make_order_with_item(db_session, "MM-ED06", kept, unit_price=880, qty=2)
    kept.price = 1000
    await db_session.flush()

    result = await admin_order_service.update_order(
        db_session,
        "MM-ED06",
        AdminOrderUpdate(
            items=[
                AdminOrderItemUpdate(spec_id=kept.id, qty=3),
                AdminOrderItemUpdate(spec_id=added.id, qty=1),
            ],
            expected_total=_total([(880, 3, False), (500, 1, False)]),
        ),
    )

    assert [(i.spec_id, i.qty, i.unit_price) for i in result.items] == [
        (kept.id, 3, 880),
        (added.id, 1, 500),
    ]
    assert result.subtotal == 880 * 3 + 500
    assert result.total == _total([(880, 3, False), (500, 1, False)])
    await db_session.refresh(kept)
    await db_session.refresh(added)
    assert kept.stock_qty == 4  # 5 - 1(只扣差額)
    assert added.stock_qty == 9


async def test_update_order_items_removes_order_item_and_restores_stock(db_session: AsyncSession):
    removed = await _make_product_and_spec(db_session, slug="removed", price=880, stock_qty=5)
    other = await _make_product_and_spec(db_session, slug="other", price=500, stock_qty=10)
    order = await _make_order_with_item(db_session, "MM-ED07", removed, unit_price=880, qty=2)
    db_session.add(
        OrderItem(order_id=order.id, product_id=other.product_id, spec_id=other.id,
                  product_name="甘露梨", spec_label="A", unit_price=500, qty=1, line_total=500)
    )
    await db_session.flush()

    result = await admin_order_service.update_order(
        db_session,
        "MM-ED07",
        AdminOrderUpdate(
            items=[AdminOrderItemUpdate(spec_id=other.id, qty=1)],
            expected_total=_total([(500, 1, False)]),
        ),
    )

    assert [i.spec_id for i in result.items] == [other.id]
    await db_session.refresh(removed)
    assert removed.stock_qty == 7


async def test_update_order_items_price_changed_writes_nothing(db_session: AsyncSession):
    spec = await _make_product_and_spec(db_session, slug="pc", price=880, stock_qty=5)
    await _make_order_with_item(db_session, "MM-ED08", spec, unit_price=880, qty=2)

    with pytest.raises(PriceChangedError):
        await admin_order_service.update_order(
            db_session,
            "MM-ED08",
            AdminOrderUpdate(
                items=[AdminOrderItemUpdate(spec_id=spec.id, qty=3)], expected_total=1
            ),
        )
    await db_session.refresh(spec)
    assert spec.stock_qty == 5


async def test_update_order_items_even_qty_violation(db_session: AsyncSession):
    spec = await _make_product_and_spec(
        db_session, slug="twopack", price=880, stock_qty=10, is_two_pack=True
    )
    order = _make_order("MM-ED09")
    db_session.add(order)
    await db_session.flush()

    with pytest.raises(EvenQtyRequiredError):
        await admin_order_service.update_order(
            db_session,
            "MM-ED09",
            AdminOrderUpdate(
                items=[AdminOrderItemUpdate(spec_id=spec.id, qty=3)],
                expected_total=_total([(880, 3, True)]),
            ),
        )


async def test_update_order_items_insufficient_stock(db_session: AsyncSession):
    spec = await _make_product_and_spec(db_session, slug="lowstock", price=880, stock_qty=1)
    order = _make_order("MM-ED10")
    db_session.add(order)
    await db_session.flush()

    with pytest.raises(InsufficientStockError):
        await admin_order_service.update_order(
            db_session,
            "MM-ED10",
            AdminOrderUpdate(
                items=[AdminOrderItemUpdate(spec_id=spec.id, qty=5)],
                expected_total=_total([(880, 5, False)]),
            ),
        )


async def test_update_order_items_unknown_spec_raises_not_found(db_session: AsyncSession):
    order = _make_order("MM-ED11")
    db_session.add(order)
    await db_session.flush()

    with pytest.raises(NotFoundError):
        await admin_order_service.update_order(
            db_session,
            "MM-ED11",
            AdminOrderUpdate(
                items=[AdminOrderItemUpdate(spec_id=999999, qty=1)], expected_total=0
            ),
        )


async def test_update_transfer_info_sets_fields_independent_of_status(
    db_session: AsyncSession,
):
    await order_repo.add(db_session, _make_order("MM-TR03", status="shipping"))
    await db_session.flush()

    result = await admin_order_service.update_transfer_info(
        db_session,
        "MM-TR03",
        AdminOrderTransferUpdate(
            transfer_last5="12345", transfer_payer_name="王小明", transfer_note="已核對"
        ),
    )
    assert result.transfer_last5 == "12345"
    assert result.transfer_payer_name == "王小明"
    assert result.transfer_note == "已核對"
    assert result.status == "shipping"  # 狀態不受影響


async def test_update_transfer_info_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.update_transfer_info(
            db_session, "MM-GHOST", AdminOrderTransferUpdate(transfer_last5="00000")
        )


async def test_cancel_restores_stock_of_inactive_spec_and_skips_deleted(
    db_session: AsyncSession,
):
    product = Product(slug="kanro3", name="甘露梨", description="d", image="i", season="s")
    db_session.add(product)
    await db_session.flush()
    gone = ProductSpec(product_id=product.id, label="下架", qty_text="q", price=800,
                       stock_qty=0, sort_order=1, is_active=False)
    db_session.add(gone)
    await db_session.flush()

    order = _make_order("MM-CANCEL3", status="ready")
    db_session.add(order)
    await db_session.flush()
    for spec_id, qty in ((gone.id, 2), (999999, 1)):
        db_session.add(OrderItem(order_id=order.id, product_id=product.id, spec_id=spec_id,
                                 product_name="甘露梨", spec_label="x", unit_price=800,
                                 qty=qty, line_total=800 * qty))
    await db_session.flush()

    result = await admin_order_service.change_order_status(db_session, "MM-CANCEL3", "cancelled")

    assert result.status == "cancelled"
    await db_session.refresh(gone)
    assert gone.stock_qty == 2
