import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InsufficientStockError,
    NotFoundError,
    PriceChangedError,
)
from app.models.order import Order
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo
from app.schemas.order import OrderCreate
from app.services import order_service


async def _seed_spec(db_session, *, price=1880, stock=10):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="5 台斤家庭箱", qty_text="q", price=price,
                    stock_qty=stock, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs[0]


def _payload(spec_id, qty, *, payment="linepay", expected_total):
    return OrderCreate.model_validate({
        "customer": {"name": "王小明", "phone": "0912345678", "email": None},
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "x", "preferred_date": "2026-10-12", "delivery_window": "any",
        },
        "items": [{"spec_id": spec_id, "qty": qty}],
        "payment_method": payment,
        "note": None,
        "expected_total": expected_total,
    })


async def _order_count(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(Order))
    return int(result.scalar_one())


async def test_create_order_success_decrements_and_snapshots(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    result = await order_service.create_order(
        db_session, _payload(spec.id, 1, expected_total=2030)
    )
    assert result.order_no.startswith("MM-")
    assert result.status == "pending_payment"
    assert result.subtotal == 1880
    assert result.shipping_fee == 150
    assert result.total == 2030
    assert result.items[0].product_name == "甘露梨"
    assert result.items[0].spec_label == "5 台斤家庭箱"
    assert result.items[0].unit_price == 1880
    assert result.items[0].line_total == 1880
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 9


async def test_create_order_cod_status_and_fee(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=6000, stock=5)
    result = await order_service.create_order(
        db_session, _payload(spec.id, 1, payment="cod", expected_total=6030)
    )
    assert result.status == "pending_payment"
    assert result.shipping_fee == 0
    assert result.cod_fee == 30
    assert result.total == 6030


async def test_price_changed_blocks_and_keeps_stock(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    with pytest.raises(PriceChangedError) as exc:
        await order_service.create_order(
            db_session, _payload(spec.id, 1, expected_total=9999)
        )
    assert exc.value.total == 2030
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 10
    assert await _order_count(db_session) == 0


async def test_insufficient_stock_blocks_and_keeps_stock(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=2)
    with pytest.raises(InsufficientStockError):
        await order_service.create_order(
            db_session, _payload(spec.id, 5, expected_total=9400)
        )
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 2
    assert await _order_count(db_session) == 0


async def test_unknown_spec_raises_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await order_service.create_order(
            db_session, _payload(999999, 1, expected_total=0)
        )


async def test_inactive_spec_raises_not_found(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    spec.is_active = False
    await db_session.flush()
    with pytest.raises(NotFoundError):
        await order_service.create_order(
            db_session, _payload(spec.id, 1, expected_total=2030)
        )
