import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.repositories import order_repo
from app.schemas.order import OrderCreate, OrderItemRead, OrderRead
from app.services import line_service, order_items

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


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


async def create_order(session: AsyncSession, data: OrderCreate) -> OrderRead:
    result = await order_items.apply_items(
        session,
        [],
        [order_items.ItemRequest(i.spec_id, i.qty) for i in data.items],
        expected_total=data.expected_total,
    )
    order_no = await generate_unique_order_no(session)

    order = Order(
        order_no=order_no,
        status=initial_status(),
        customer_name=data.customer.name,
        customer_phone=data.customer.phone,
        customer_email=data.customer.email,
        line_user_id=data.customer.line_user_id,
        line_display_name=data.customer.line_display_name,
        line_picture_url=data.customer.line_picture_url,
        line_friendship_status=data.customer.line_friendship_status,
        line_notification_consent=data.customer.line_notification_consent,
        ship_zipcode=data.shipping.zipcode,
        ship_city=data.shipping.city,
        ship_district=data.shipping.district,
        ship_street=data.shipping.street,
        preferred_date=data.shipping.preferred_date,
        delivery_window=data.shipping.delivery_window,
        payment_method=data.payment_method,
        note=data.note,
    )
    result.apply_to(order)
    await order_repo.add(session, order)
    await session.commit()
    await session.refresh(order)
    await line_service.send_order_created(order)
    return _to_order_read(order)
