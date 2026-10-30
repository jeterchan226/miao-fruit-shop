import secrets
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    ORDER_SOURCE_STOREFRONT,
    OrderSource,
    PaymentMethod,
)
from app.models.order import Order
from app.repositories import order_repo
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderRead,
    ShippingCreate,
)
from app.services import line_service, order_items

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@dataclass(frozen=True)
class OrderCustomer:
    """建立訂單用的顧客資料。不做驗證,請求驗證留在 schema 層。"""

    name: str
    phone: str
    email: str | None = None
    line_user_id: str | None = None
    line_display_name: str | None = None
    line_picture_url: str | None = None
    line_friendship_status: str | None = None
    line_notification_consent: bool = False


def initial_status() -> str:
    # 轉帳訂單一律從待付款開始。
    return "pending_payment"


def _new_order_no() -> str:
    suffix = "".join(secrets.choice(ORDER_NO_ALPHABET) for _ in range(6))
    return f"MM-{suffix}"


async def generate_unique_order_no(session: AsyncSession) -> str:
    for _ in range(5):
        candidate = _new_order_no()
        if await order_repo.get_by_order_no(session, candidate) is None:
            return candidate
    raise RuntimeError("無法產生唯一訂單編號")


def _to_order_read(order: Order) -> OrderRead:
    return OrderRead(
        order_no=order.order_no,
        status=order.status,
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
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee,
        cod_fee=order.cod_fee,
        total=order.total,
        created_at=order.created_at,
    )


async def place_order(
    session: AsyncSession,
    *,
    source: OrderSource,
    customer: OrderCustomer,
    shipping: ShippingCreate,
    items: list[OrderItemCreate],
    expected_total: int,
    payment_method: PaymentMethod,
    note: str | None,
) -> Order:
    """顧客下單與代客下單共用:扣庫存、核對金額、成立訂單並提交。不發通知。"""
    result = await order_items.apply_items(
        session,
        [],
        [order_items.ItemRequest(i.spec_id, i.qty) for i in items],
        expected_total=expected_total,
    )
    order = Order(
        order_no=await generate_unique_order_no(session),
        status=initial_status(),
        source=source,
        customer_name=customer.name,
        customer_phone=customer.phone,
        customer_email=customer.email,
        line_user_id=customer.line_user_id,
        line_display_name=customer.line_display_name,
        line_picture_url=customer.line_picture_url,
        line_friendship_status=customer.line_friendship_status,
        line_notification_consent=customer.line_notification_consent,
        ship_zipcode=shipping.zipcode,
        ship_city=shipping.city,
        ship_district=shipping.district,
        ship_street=shipping.street,
        preferred_date=shipping.preferred_date,
        delivery_window=shipping.delivery_window,
        payment_method=payment_method,
        note=note,
    )
    result.apply_to(order)
    await order_repo.add(session, order)
    await session.commit()
    await session.refresh(order)
    return order


async def create_order(session: AsyncSession, data: OrderCreate) -> OrderRead:
    order = await place_order(
        session,
        source=ORDER_SOURCE_STOREFRONT,
        customer=OrderCustomer(
            name=data.customer.name,
            phone=data.customer.phone,
            email=data.customer.email,
            line_user_id=data.customer.line_user_id,
            line_display_name=data.customer.line_display_name,
            line_picture_url=data.customer.line_picture_url,
            line_friendship_status=data.customer.line_friendship_status,
            line_notification_consent=data.customer.line_notification_consent,
        ),
        shipping=data.shipping,
        items=data.items,
        expected_total=data.expected_total,
        payment_method=data.payment_method,
        note=data.note,
    )
    await line_service.send_order_created(order)
    return _to_order_read(order)
