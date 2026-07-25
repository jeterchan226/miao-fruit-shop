import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EvenQtyRequiredError,
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
from app.services.order_service import compute_amounts, compute_layers, compute_shipping


async def _seed_spec(db_session, *, price=1880, stock=10):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="5 台斤家庭箱", qty_text="q", price=price,
                    stock_qty=stock, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs[0]


async def _seed_two_pack_spec(db_session, *, price=600, stock=10):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="2 粒裝", qty_text="q", price=price,
                    stock_qty=stock, sort_order=1, is_two_pack=True)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs[0]


def _payload(spec_id, qty, *, payment="transfer", expected_total):
    return OrderCreate.model_validate({
        "customer": {
            "name": "王小明",
            "phone": "0912345678",
            "email": None,
            "line_user_id": "U123",
            "line_display_name": "小明",
            "line_picture_url": "https://example.com/line.jpg",
            "line_friendship_status": "friend",
            "line_notification_consent": True,
        },
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


def test_layers_non_two_pack_one_per_box():
    assert compute_layers([(700, 3, False)]) == 3


def test_layers_two_pack_two_boxes_one_layer():
    assert compute_layers([(600, 4, True)]) == 2


def test_layers_mixed():
    assert compute_layers([(700, 1, False), (600, 2, True)]) == 2


def test_shipping_by_layer():
    assert compute_shipping(1000, 1) == 100
    assert compute_shipping(1000, 2) == 150
    assert compute_shipping(1000, 3) == 180
    assert compute_shipping(1000, 4) == 180  # >3 fallback


def test_shipping_free_over_threshold():
    assert compute_shipping(3000, 3) == 0


def test_shipping_zero_layers():
    assert compute_shipping(0, 0) == 0


def test_compute_amounts_mixed():
    amt = compute_amounts([(700, 1, False), (600, 2, True)])  # subtotal 1900, layers 2
    assert amt.subtotal == 1900
    assert amt.shipping_fee == 150
    assert amt.total == 2050


async def test_create_order_success_decrements_and_snapshots(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    result = await order_service.create_order(
        db_session, _payload(spec.id, 1, expected_total=1980)
    )
    assert result.order_no.startswith("MM-")
    assert result.status == "pending_payment"
    assert result.subtotal == 1880
    assert result.shipping_fee == 100
    assert result.total == 1980
    assert result.items[0].product_name == "甘露梨"
    assert result.items[0].spec_label == "5 台斤家庭箱"
    assert result.items[0].unit_price == 1880
    assert result.items[0].line_total == 1880
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 9
    saved = (await db_session.execute(select(Order))).scalars().one()
    assert saved.line_user_id == "U123"
    assert saved.line_display_name == "小明"
    assert saved.line_notification_consent is True


async def test_create_order_free_shipping_no_cod_fee(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=6000, stock=5)
    result = await order_service.create_order(
        db_session, _payload(spec.id, 1, expected_total=6000)
    )
    assert result.status == "pending_payment"
    assert result.shipping_fee == 0
    assert result.cod_fee == 0
    assert result.total == 6000


async def test_price_changed_blocks_and_keeps_stock(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    with pytest.raises(PriceChangedError) as exc:
        await order_service.create_order(
            db_session, _payload(spec.id, 1, expected_total=9999)
        )
    assert exc.value.total == 1980
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


async def test_two_pack_odd_qty_rejected(db_session: AsyncSession):
    spec = await _seed_two_pack_spec(db_session, price=600, stock=10)
    with pytest.raises(EvenQtyRequiredError):
        await order_service.create_order(
            db_session, _payload(spec.id, 3, expected_total=600 * 3 + 180)
        )


async def test_two_pack_even_qty_ok(db_session: AsyncSession):
    spec = await _seed_two_pack_spec(db_session, price=600, stock=10)
    result = await order_service.create_order(
        db_session, _payload(spec.id, 4, expected_total=2400 + 150)
    )
    assert result.order_no.startswith("MM-")
    assert result.subtotal == 2400
    assert result.shipping_fee == 150
    assert result.total == 2550
