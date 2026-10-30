from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidStatusTransition,
    NotFoundError,
    OrderNotEditableError,
)
from app.models.order import Order
from app.repositories import order_repo
from app.schemas.order import (
    ADMIN_ORDER_REQUIRED_FIELDS,
    AdminOrderCreate,
    AdminOrderListItem,
    AdminOrderListResponse,
    AdminOrderRead,
    AdminOrderSummary,
    AdminOrderTransferUpdate,
    AdminOrderUpdate,
    OrderItemRead,
)
from app.services import order_items, order_service

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending_payment": {"ready", "cancelled"},      # 待付款
    "ready":           {"shipping", "cancelled"},   # 待出貨
    "shipping":        set(),                        # 已出貨(終態)
    "cancelled":       set(),                        # 已取消
}

# 出貨後/已取消的訂單不可再編輯內容(仍可填轉帳資訊)。
NOT_EDITABLE_STATUSES: set[str] = {"shipping", "cancelled"}

# 必填欄位與 AdminOrderUpdate 的 null 檢查共用同一份清單
_SIMPLE_UPDATE_FIELDS = (*ADMIN_ORDER_REQUIRED_FIELDS, "customer_email", "note")


def _to_admin_list_item(order: Order) -> AdminOrderListItem:
    return AdminOrderListItem(
        order_no=order.order_no,
        status=order.status,
        source=order.source,
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
        source=order.source,
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
    source: str | None = None,
    created_from: datetime | None = None,
    created_before: datetime | None = None,
    q: str | None = None,
    order_no: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AdminOrderListResponse:
    total, orders = await order_repo.list_filtered(
        session,
        status=status,
        source=source,
        created_from=created_from,
        created_before=created_before,
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


async def create_order(session: AsyncSession, data: AdminOrderCreate) -> AdminOrderRead:
    """代客下單:規則同顧客下單,但來源記為 admin、無 LINE 身份、不發 LINE 通知。"""
    result = await order_items.apply_items(
        session,
        [],
        [order_items.ItemRequest(i.spec_id, i.qty) for i in data.items],
        expected_total=data.expected_total,
    )
    order = Order(
        order_no=await order_service.generate_unique_order_no(session),
        status=order_service.initial_status(),
        source="admin",
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        ship_zipcode=data.shipping.zipcode,
        ship_city=data.shipping.city,
        ship_district=data.shipping.district,
        ship_street=data.shipping.street,
        preferred_date=data.shipping.preferred_date,
        delivery_window=data.shipping.delivery_window,
        payment_method="transfer",
        note=data.note,
    )
    result.apply_to(order)
    await order_repo.add(session, order)
    await session.commit()
    await session.refresh(order)
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
        await order_items.release_items(session, order.items)
    order.status = new_status
    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)


async def update_order(
    session: AsyncSession, order_no: str, data: AdminOrderUpdate
) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")
    if order.status in NOT_EDITABLE_STATUSES:
        raise OrderNotEditableError(f"訂單狀態為 {order.status},無法編輯")

    # 只更新請求中有送的欄位;明確送 null 代表清空(必填欄位送 null 已由 schema 擋下)
    fields = data.model_dump(include=set(_SIMPLE_UPDATE_FIELDS), exclude_unset=True)
    for field, value in fields.items():
        setattr(order, field, value)

    if data.items is not None:
        if data.expected_total is None:  # schema 已擋下,此處僅防禦
            raise ValueError("送出訂單品項時須附 expected_total")
        result = await order_items.apply_items(
            session,
            order.items,
            [order_items.ItemRequest(i.spec_id, i.qty) for i in data.items],
            expected_total=data.expected_total,
        )
        result.apply_to(order)

    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)


async def update_transfer_info(
    session: AsyncSession, order_no: str, data: AdminOrderTransferUpdate
) -> AdminOrderRead:
    order = await order_repo.get_by_order_no(session, order_no)
    if order is None:
        raise NotFoundError("找不到訂單")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(order, field, value)

    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)
