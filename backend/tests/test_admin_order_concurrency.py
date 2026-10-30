"""並行改動同一筆訂單:兩個 session 各自 commit,驗證訂單列鎖讓庫存只異動一次。

db_session fixture 是單一連線 + rollback 的交易,無法模擬兩條連線互相等待,
因此這裡直接用 engine 開兩個 session,資料真的 commit,測試結束後自行刪除。
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import date as date_type
from typing import NamedTuple

import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.exceptions import InvalidStatusTransition
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.schemas.order import AdminOrderItemUpdate, AdminOrderUpdate
from app.services import admin_order_service

_SLUG = "kanro-race"
_ORDER_NO = "MM-RACE01"
# 鎖若出錯(例如互相等待)會讓 gather 卡住;逾時改為測試失敗
_RACE_TIMEOUT_S = 10


class Seeded(NamedTuple):
    order_no: str
    spec_id: int
    other_spec_id: int  # 規格 B,訂單原本沒有


@pytest_asyncio.fixture(loop_scope="session")
async def committing_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="session")
async def seeded(
    committing_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[Seeded]:
    """已 commit 的待付款訂單:規格 A(單價 880、庫存 10)× 2;另有規格 B(單價 880、庫存 10)。"""
    async with committing_sessionmaker() as s:
        # 先清掉上次被中斷(未跑到 teardown)留下的資料,否則 unique 衝突、也會污染其他測試
        await _delete_seeded(s)
        product = Product(
            slug=_SLUG, name="甘露梨", description="d", image="i", season="s"
        )
        s.add(product)
        await s.flush()
        spec = ProductSpec(
            product_id=product.id,
            label="A",
            qty_text="q",
            price=880,
            stock_qty=10,
            sort_order=1,
        )
        other_spec = ProductSpec(
            product_id=product.id,
            label="B",
            qty_text="q",
            price=880,
            stock_qty=10,
            sort_order=2,
        )
        s.add_all([spec, other_spec])
        await s.flush()
        order = Order(
            order_no=_ORDER_NO,
            status="pending_payment",
            customer_name="王小明",
            customer_phone="0912345678",
            customer_email=None,
            ship_zipcode="100",
            ship_city="台北市",
            ship_district="中正區",
            ship_street="重慶南路1號",
            preferred_date=date_type(2026, 10, 1),
            delivery_window="any",
            payment_method="transfer",
            note=None,
            subtotal=1760,
            shipping_fee=0,
            cod_fee=0,
            total=1760,
        )
        order.items = [
            OrderItem(
                product_id=product.id,
                spec_id=spec.id,
                product_name="甘露梨",
                spec_label="A",
                unit_price=880,
                qty=2,
                line_total=1760,
            )
        ]
        s.add(order)
        await s.commit()
        seeded = Seeded(
            order_no=order.order_no, spec_id=spec.id, other_spec_id=other_spec.id
        )
    try:
        yield seeded
    finally:
        async with committing_sessionmaker() as s:
            await _delete_seeded(s)


async def _delete_seeded(s: AsyncSession) -> None:
    order_ids = select(Order.id).where(Order.order_no == _ORDER_NO)
    product_ids = select(Product.id).where(Product.slug == _SLUG)
    await s.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    await s.execute(delete(Order).where(Order.order_no == _ORDER_NO))
    await s.execute(delete(ProductSpec).where(ProductSpec.product_id.in_(product_ids)))
    await s.execute(delete(Product).where(Product.slug == _SLUG))
    await s.commit()


async def _stock(committing_sessionmaker: async_sessionmaker[AsyncSession], spec_id: int) -> int:
    async with committing_sessionmaker() as s:
        spec = await s.get(ProductSpec, spec_id)
        assert spec is not None
        return spec.stock_qty


async def test_concurrent_cancel_restores_stock_once(
    committing_sessionmaker: async_sessionmaker[AsyncSession], seeded: Seeded
):
    async def cancel() -> None:
        async with committing_sessionmaker() as s:
            await admin_order_service.change_order_status(s, seeded.order_no, "cancelled")

    results = await asyncio.wait_for(
        asyncio.gather(cancel(), cancel(), return_exceptions=True), _RACE_TIMEOUT_S
    )

    assert results.count(None) == 1
    assert sum(isinstance(r, InvalidStatusTransition) for r in results) == 1
    assert await _stock(committing_sessionmaker, seeded.spec_id) == 12


async def test_concurrent_edit_adjusts_stock_once(
    committing_sessionmaker: async_sessionmaker[AsyncSession], seeded: Seeded
):
    # 兩個請求都把 A × 2 改成 A × 4(總價 3520,滿額免運):應只多扣 2
    data = AdminOrderUpdate(
        items=[AdminOrderItemUpdate(spec_id=seeded.spec_id, qty=4)], expected_total=3520
    )

    async def edit() -> None:
        async with committing_sessionmaker() as s:
            await admin_order_service.update_order(s, seeded.order_no, data)

    results = await asyncio.wait_for(
        asyncio.gather(edit(), edit(), return_exceptions=True), _RACE_TIMEOUT_S
    )

    assert results == [None, None]
    assert await _stock(committing_sessionmaker, seeded.spec_id) == 8


async def test_concurrent_edit_restores_removed_item_stock_once(
    committing_sessionmaker: async_sessionmaker[AsyncSession], seeded: Seeded
):
    # 兩個請求都把 A × 2 換成 B × 1(880 + 運費 100):A 只補回 2、B 只扣 1
    data = AdminOrderUpdate(
        items=[AdminOrderItemUpdate(spec_id=seeded.other_spec_id, qty=1)], expected_total=980
    )

    async def edit() -> None:
        async with committing_sessionmaker() as s:
            await admin_order_service.update_order(s, seeded.order_no, data)

    results = await asyncio.wait_for(
        asyncio.gather(edit(), edit(), return_exceptions=True), _RACE_TIMEOUT_S
    )

    assert results == [None, None]
    assert await _stock(committing_sessionmaker, seeded.spec_id) == 12
    assert await _stock(committing_sessionmaker, seeded.other_spec_id) == 9
