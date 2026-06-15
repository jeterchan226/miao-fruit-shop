import secrets
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import COD_FEE, FREE_SHIPPING_THRESHOLD, SHIPPING_FEE
from app.core.exceptions import (
    InsufficientStockError,
    NotFoundError,
    PriceChangedError,
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_spec import ProductSpec
from app.repositories import order_repo, spec_repo
from app.schemas.order import OrderCreate, OrderItemRead, OrderRead

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class Amounts(NamedTuple):
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int


def compute_amounts(subtotal: int, payment_method: str) -> Amounts:
    shipping_fee = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
    cod_fee = COD_FEE if payment_method == "cod" else 0
    return Amounts(
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        cod_fee=cod_fee,
        total=subtotal + shipping_fee + cod_fee,
    )


def initial_status(payment_method: str) -> str:
    return "ready" if payment_method == "cod" else "pending_payment"


def _new_order_no() -> str:
    suffix = "".join(secrets.choice(ORDER_NO_ALPHABET) for _ in range(6))
    return f"MM-{suffix}"


async def _generate_unique_order_no(session: AsyncSession) -> str:
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
    # 1) 行鎖讀取每個規格並驗證存在/啟用
    locked: list[tuple[ProductSpec, int]] = []
    for item in data.items:
        spec = await spec_repo.get_for_update(session, item.spec_id)
        if spec is None or not spec.is_active:
            raise NotFoundError(f"找不到規格 {item.spec_id}")
        locked.append((spec, item.qty))

    # 2) 伺服器權威重算金額
    subtotal = sum(spec.price * qty for spec, qty in locked)
    amounts = compute_amounts(subtotal, data.payment_method)

    # 3) 價格確認:與前端顯示的 expected_total 不符 → 擋下,回新明細
    if amounts.total != data.expected_total:
        raise PriceChangedError(
            "商品價格已更新,請重新確認",
            subtotal=amounts.subtotal,
            shipping_fee=amounts.shipping_fee,
            cod_fee=amounts.cod_fee,
            total=amounts.total,
        )

    # 4) 驗庫存(扣減前先全部檢查)
    for spec, qty in locked:
        if spec.stock_qty < qty:
            raise InsufficientStockError(f"庫存不足:{spec.label}")

    # 5) 扣庫存 + 建單(快照品名/規格/單價)
    order_no = await _generate_unique_order_no(session)
    for spec, qty in locked:
        spec.stock_qty -= qty

    order = Order(
        order_no=order_no,
        status=initial_status(data.payment_method),
        customer_name=data.customer.name,
        customer_phone=data.customer.phone,
        customer_email=data.customer.email,
        ship_zipcode=data.shipping.zipcode,
        ship_city=data.shipping.city,
        ship_district=data.shipping.district,
        ship_street=data.shipping.street,
        preferred_date=data.shipping.preferred_date,
        delivery_window=data.shipping.delivery_window,
        payment_method=data.payment_method,
        note=data.note,
        subtotal=amounts.subtotal,
        shipping_fee=amounts.shipping_fee,
        cod_fee=amounts.cod_fee,
        total=amounts.total,
    )
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
    await order_repo.add(session, order)
    await session.commit()
    await session.refresh(order)
    return _to_order_read(order)
