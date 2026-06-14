from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStatusTransition, NotFoundError
from app.models.order import Order
from app.repositories import order_repo, spec_repo
from app.schemas.order import (
    AdminOrderListItem,
    AdminOrderListResponse,
    AdminOrderRead,
    OrderItemRead,
)

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":         {"confirmed", "cancelled"},
    "pending_payment": {"confirmed", "cancelled"},
    "confirmed":       {"shipping", "cancelled"},
    "shipping":        {"delivered"},
    "delivered":       set(),
    "cancelled":       set(),
}


def _to_admin_list_item(order: Order) -> AdminOrderListItem:
    return AdminOrderListItem(
        order_no=order.order_no,
        status=order.status,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        total=order.total,
        created_at=order.created_at,
    )


def _to_admin_order_read(order: Order) -> AdminOrderRead:
    return AdminOrderRead(
        id=order.id,
        order_no=order.order_no,
        status=order.status,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_email=order.customer_email,
        ship_zipcode=order.ship_zipcode,
        ship_city=order.ship_city,
        ship_district=order.ship_district,
        ship_street=order.ship_street,
        preferred_date=order.preferred_date,
        delivery_window=order.delivery_window,
        payment_method=order.payment_method,
        note=order.note,
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        cod_fee=order.cod_fee,
        total=order.total,
        items=[
            OrderItemRead(
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
    return AdminOrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_admin_list_item(o) for o in orders],
    )


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
