"""相同 Idempotency-Key 同時送達:兩個 session 各自 commit,驗證只成立一張訂單。

db_session fixture 是單一連線 + rollback 的交易,無法模擬兩條連線互相等待,
因此這裡直接用 engine 開兩個 session,資料真的 commit,測試結束後自行刪除。
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import date as date_type

import pytest
import pytest_asyncio
from pytest import MonkeyPatch
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.exceptions import InsufficientStockError
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.schemas.order import (
    CustomerCreate,
    OrderCreate,
    OrderItemCreate,
    OrderRead,
    ShippingCreate,
)
from app.services import line_service, order_service

_SLUG = "kanro-idempotency-race"
_KEY = "race-key"
_OTHER_KEY = "race-key-other"
# 鎖若出錯(例如互相等待)會讓 gather 卡住;逾時改為測試失敗
_RACE_TIMEOUT_S = 10


@pytest_asyncio.fixture(loop_scope="session")
async def committing_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def _delete_seeded(s: AsyncSession) -> None:
    order_ids = select(Order.id).where(Order.idempotency_key.in_([_KEY, _OTHER_KEY]))
    product_ids = select(Product.id).where(Product.slug == _SLUG)
    await s.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    await s.execute(delete(Order).where(Order.idempotency_key.in_([_KEY, _OTHER_KEY])))
    await s.execute(delete(ProductSpec).where(ProductSpec.product_id.in_(product_ids)))
    await s.execute(delete(Product).where(Product.slug == _SLUG))
    await s.commit()


async def _seed_spec(
    sessionmaker: async_sessionmaker[AsyncSession], *, stock: int
) -> int:
    async with sessionmaker() as s:
        product = Product(slug=_SLUG, name="甘露梨", description="d", image="i", season="s")
        spec = ProductSpec(
            label="A", qty_text="q", price=880, stock_qty=stock, sort_order=1
        )
        product.specs = [spec]
        s.add(product)
        await s.commit()
        return spec.id


@pytest_asyncio.fixture(loop_scope="session")
async def clean_seed(
    committing_sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[None]:
    async with committing_sessionmaker() as s:
        # 先清掉上次被中斷(未跑到 teardown)留下的資料,否則 unique 衝突、也會污染其他測試
        await _delete_seeded(s)
    try:
        yield
    finally:
        async with committing_sessionmaker() as s:
            await _delete_seeded(s)


def _order_create(spec_id: int) -> OrderCreate:
    return OrderCreate(
        customer=CustomerCreate(name="王小明", phone="0912345678"),
        shipping=ShippingCreate(
            zipcode="100",
            city="台北市",
            district="中正區",
            street="重慶南路1號",
            preferred_date=date_type(2026, 12, 1),
            delivery_window="any",
        ),
        items=[OrderItemCreate(spec_id=spec_id, qty=1)],
        payment_method="transfer",
        note=None,
        expected_total=980,
    )


async def _submit(
    sessionmaker: async_sessionmaker[AsyncSession], spec_id: int, key: str
) -> OrderRead:
    async with sessionmaker() as s:
        return await order_service.create_order(s, _order_create(spec_id), key)


async def _stock_and_order_count(
    sessionmaker: async_sessionmaker[AsyncSession], spec_id: int
) -> tuple[int, int]:
    async with sessionmaker() as s:
        spec = await s.get(ProductSpec, spec_id)
        assert spec is not None
        count = await s.scalar(
            select(func.count()).select_from(Order).where(Order.idempotency_key == _KEY)
        )
        assert count is not None
        return spec.stock_qty, count


@pytest.mark.usefixtures("clean_seed")
async def test_same_key_concurrent_creates_one_order(
    committing_sessionmaker: async_sessionmaker[AsyncSession], monkeypatch: MonkeyPatch
):
    notified: list[str] = []

    async def _record(order: Order) -> bool:
        notified.append(order.order_no)
        return True

    monkeypatch.setattr(line_service, "send_order_created", _record)
    spec_id = await _seed_spec(committing_sessionmaker, stock=10)

    first, second = await asyncio.wait_for(
        asyncio.gather(
            _submit(committing_sessionmaker, spec_id, _KEY),
            _submit(committing_sessionmaker, spec_id, _KEY),
        ),
        _RACE_TIMEOUT_S,
    )

    assert first.order_no == second.order_no
    assert notified == [first.order_no]
    assert await _stock_and_order_count(committing_sessionmaker, spec_id) == (9, 1)


@pytest.mark.usefixtures("clean_seed")
async def test_same_key_concurrent_for_last_stock_creates_one_order(
    committing_sessionmaker: async_sessionmaker[AsyncSession],
):
    # 輸家等到規格列鎖時庫存已歸零,拋的是 InsufficientStockError 而非唯一約束錯誤
    spec_id = await _seed_spec(committing_sessionmaker, stock=1)

    first, second = await asyncio.wait_for(
        asyncio.gather(
            _submit(committing_sessionmaker, spec_id, _KEY),
            _submit(committing_sessionmaker, spec_id, _KEY),
        ),
        _RACE_TIMEOUT_S,
    )

    assert first.order_no == second.order_no
    assert await _stock_and_order_count(committing_sessionmaker, spec_id) == (0, 1)


@pytest.mark.usefixtures("clean_seed")
async def test_different_key_concurrent_for_last_stock_still_fails(
    committing_sessionmaker: async_sessionmaker[AsyncSession],
):
    # 再查不到原訂單時,業務錯誤照常拋出
    spec_id = await _seed_spec(committing_sessionmaker, stock=1)

    results = await asyncio.wait_for(
        asyncio.gather(
            _submit(committing_sessionmaker, spec_id, _KEY),
            _submit(committing_sessionmaker, spec_id, _OTHER_KEY),
            return_exceptions=True,
        ),
        _RACE_TIMEOUT_S,
    )

    assert sum(isinstance(r, OrderRead) for r in results) == 1
    assert sum(isinstance(r, InsufficientStockError) for r in results) == 1
