from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EvenQtyRequiredError,
    InsufficientStockError,
    InvalidStatusTransition,
    NotFoundError,
    OrderNotEditableError,
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_spec import ProductSpec
from app.repositories import order_repo, spec_repo
from app.schemas.order import (
    AdminOrderItemUpdate,
    AdminOrderListItem,
    AdminOrderListResponse,
    AdminOrderRead,
    AdminOrderSummary,
    AdminOrderTransferUpdate,
    AdminOrderUpdate,
    OrderItemRead,
)
from app.services import order_service

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending_payment": {"ready", "cancelled"},      # 待付款
    "ready":           {"shipping", "cancelled"},   # 待出貨
    "shipping":        set(),                        # 已出貨(終態)
    "cancelled":       set(),                        # 已取消
}

# 出貨後/已取消的訂單不可再編輯內容(仍可填轉帳資訊)。
NOT_EDITABLE_STATUSES: set[str] = {"shipping", "cancelled"}

_SIMPLE_UPDATE_FIELDS = (
    "customer_name",
    "customer_phone",
    "customer_email",
    "ship_zipcode",
    "ship_city",
    "ship_district",
    "ship_street",
    "preferred_date",
    "delivery_window",
    "note",
)

_TRANSFER_UPDATE_FIELDS = ("transfer_last5", "transfer_payer_name", "transfer_note")


def _to_admin_list_item(order: Order) -> AdminOrderListItem:
    return AdminOrderListItem(
        order_no=order.order_no,
        status=order.status,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        total=order.total,
        created_at=order.created_at,
        first_item_name=order.items[0].product_name if order.items else None,
        item_count=len(order.items),
    )


def _to_admin_order_read(order: Order) -> AdminOrderRead:
    return AdminOrderRead(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_email=order.customer_email,
        line_user_id=order.line_user_id,
        line_display_name=order.line_display_name,
        line_picture_url=order.line_picture_url,
        line_friendship_status=order.line_friendship_status,
        line_notification_consent=order.line_notification_consent,
        ship_zipcode=order.ship_zipcode,
        ship_city=order.ship_city,
        ship_district=order.ship_district,
        ship_street=order.ship_street,
        preferred_date=order.preferred_date,
        delivery_window=order.delivery_window,
        payment_method=order.payment_method,
        note=order.note,
        transfer_last5=order.transfer_last5,
        transfer_payer_name=order.transfer_payer_name,
        transfer_note=order.transfer_note,
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        cod_fee=order.cod_fee,
        total=order.total,
        items=[
            OrderItemRead(
                spec_id=i.spec_id,
                product_name=i.product_name,
                spec_label=i.spec_label,
                unit_price=i.unit_price,
                qty=i.qty,
                line_total=i.line_total,
            )
            for i in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


async def list_orders(
    session: AsyncSession,
    *,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    order_no: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AdminOrderListResponse:
    total, orders = await order_repo.list_filtered(
        session,
        status=status,
        date_from=date_from,
        date_to=date_to,
        q=q,
        order_no=order_no,
        page=page,
        page_size=page_size,
    )
    status_counts = await order_repo.count_by_status(session)
    return AdminOrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_admin_list_item(o) for o in orders],
        status_counts=status_counts,
    )


async def get_summary(session: AsyncSession) -> AdminOrderSummary:
    return AdminOrderSummary(**await order_repo.summary(session))


async def get_order_detail(session: AsyncSession, order_no: str) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")
    return _to_admin_order_read(order)


async def change_order_status(
    session: AsyncSession, order_no: str, new_status: str
) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")
    allowed = VALID_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise InvalidStatusTransition(f"無法從 {order.status} 轉移到 {new_status}")
    if new_status == "cancelled":
        for item in order.items:
            if item.spec_id is not None:
                spec = await spec_repo.get_for_update(session, item.spec_id)
                if spec is not None:
                    spec.stock_qty += item.qty
    order.status = new_status
    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)


async def _replace_items(
    session: AsyncSession, order: Order, new_items: list[AdminOrderItemUpdate]
) -> None:
    # 1) 舊品項先加回庫存
    for item in order.items:
        if item.spec_id is not None:
            spec = await spec_repo.get_for_update(session, item.spec_id)
            if spec is not None:
                spec.stock_qty += item.qty

    # 2) 鎖定新品項規格,驗證存在/啟用/2 粒裝雙數
    locked: list[tuple[ProductSpec, int]] = []
    for new_item in new_items:
        spec = await spec_repo.get_for_update(session, new_item.spec_id)
        if spec is None or not spec.is_active:
            raise NotFoundError(f"找不到規格 {new_item.spec_id}")
        if spec.is_two_pack and new_item.qty % 2 != 0:
            raise EvenQtyRequiredError(f"{spec.label} 為 2 粒裝，請以雙數（2、4、6…）購買")
        locked.append((spec, new_item.qty))

    # 3) 驗庫存(此時舊品項已加回)
    for spec, qty in locked:
        if spec.stock_qty < qty:
            raise InsufficientStockError(f"庫存不足:{spec.label}")

    # 4) 扣新庫存、以現價快照換品項
    for spec, qty in locked:
        spec.stock_qty -= qty

    order.items = [
        OrderItem(
            product_id=spec.product_id,
            spec_id=spec.id,
            product_name=spec.product.name,
            spec_label=spec.label,
            unit_price=spec.price,
            qty=qty,
            line_total=spec.price * qty,
        )
        for spec, qty in locked
    ]

    amounts = order_service.compute_amounts(
        [(spec.price, qty, spec.is_two_pack) for spec, qty in locked]
    )
    order.subtotal = amounts.subtotal
    order.shipping_fee = amounts.shipping_fee
    order.cod_fee = amounts.cod_fee
    order.total = amounts.total


async def update_order(
    session: AsyncSession, order_no: str, data: AdminOrderUpdate
) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")
    if order.status in NOT_EDITABLE_STATUSES:
        raise OrderNotEditableError(f"訂單狀態為 {order.status},無法編輯")

    for field in _SIMPLE_UPDATE_FIELDS:
        value = getattr(data, field)
        if value is not None:
            setattr(order, field, value)

    if data.items is not None:
        await _replace_items(session, order, data.items)

    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)


async def update_transfer_info(
    session: AsyncSession, order_no: str, data: AdminOrderTransferUpdate
) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")

    for field in _TRANSFER_UPDATE_FIELDS:
        value = getattr(data, field)
        if value is not None:
            setattr(order, field, value)

    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)
