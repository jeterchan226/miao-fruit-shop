# Phase 4b: Admin Order Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 為後台管理員加入訂單列表（含篩選 + 分頁）、單筆明細、改狀態（狀態機驗證 + 取消自動回補庫存）三個 endpoint。

**Architecture:** 三層 FastAPI，與 Phase 3 / 4a 完全相同。新增獨立的 `admin_order_service.py`（list / detail / change_status）與 `admin_orders.py` route；`order_service.py`（Phase 4a `create_order`）完全不動。狀態機以字典定義在 `admin_order_service.py` 頂部，取消訂單時對每筆 `order_item` 自動回補 `spec.stock_qty`。

**Tech Stack:** Python 3.13, FastAPI 0.136.3, SQLAlchemy 2.0.50 async, Pydantic 2.13.4; pytest + pytest-asyncio + httpx。

**Spec:** `docs/superpowers/specs/2026-06-14-phase4b-admin-orders-design.md`.

**Branch:** `feat/phase4b-admin-orders`（built on Phase 4a）。All commands run from `backend/`.

**Prerequisite:** PostgreSQL 17 up（`docker compose up -d db`）；Phase 4a migrations applied（`orders` + `order_items` tables exist）。

---

## File Structure

Create:
- `app/services/admin_order_service.py` — 狀態機 dict、list / detail / change_status、stock 回補
- `app/api/routes/admin_orders.py` — 3 個 endpoint（JWT 保護）
- `tests/test_schemas_admin_order.py`
- `tests/test_admin_order_service.py`
- `tests/test_admin_orders_api.py`

Modify:
- `app/schemas/order.py` — 加 `AdminOrderListItem`、`AdminOrderListResponse`、`AdminOrderRead`、`OrderStatusUpdate`
- `app/repositories/order_repo.py` — 加 `list_filtered`
- `app/main.py` — include `admin_orders` router

---

## Task 1: Admin Order Schemas

**Files:**
- Modify: `app/schemas/order.py`
- Create: `tests/test_schemas_admin_order.py`

- [x] **Step 1: Write the failing test** — `tests/test_schemas_admin_order.py`

```python
import pytest
from pydantic import ValidationError

from app.schemas.order import (
    AdminOrderListResponse,
    AdminOrderRead,
    OrderRead,
    OrderStatusUpdate,
)


def test_admin_order_read_has_admin_only_fields():
    fields = set(AdminOrderRead.model_fields)
    assert {"id", "customer_email", "ship_city", "updated_at", "items"} <= fields


def test_public_order_read_has_no_admin_fields():
    fields = set(OrderRead.model_fields)
    assert "customer_name" not in fields
    assert "ship_city" not in fields
    assert "updated_at" not in fields


def test_admin_order_list_response_structure():
    resp = AdminOrderListResponse(total=0, page=1, page_size=20, items=[])
    assert resp.total == 0
    assert resp.items == []


def test_order_status_update_forbids_extra():
    with pytest.raises(ValidationError):
        OrderStatusUpdate(status="confirmed", extra_field="oops")
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schemas_admin_order.py -v`
Expected: FAIL — `ImportError: cannot import name 'AdminOrderListResponse' from 'app.schemas.order'`

- [x] **Step 3: Append admin schemas to `app/schemas/order.py`**

Add these imports at the top of the file (the file already has `from datetime import date, datetime` and `from pydantic import BaseModel, ConfigDict, Field`):

```python
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
```

Append the following four classes **at the end** of `app/schemas/order.py`（保留所有既有 class 不動）：

```python
class AdminOrderListItem(BaseModel):
    order_no: str
    status: str
    customer_name: str
    customer_phone: str
    total: int
    created_at: datetime


class AdminOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminOrderListItem]


class AdminOrderRead(BaseModel):
    id: int
    order_no: str
    status: str
    customer_name: str
    customer_phone: str
    customer_email: str | None
    ship_zipcode: str
    ship_city: str
    ship_district: str
    ship_street: str
    preferred_date: date
    delivery_window: str
    payment_method: str
    note: str | None
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_schemas_admin_order.py -v`
Expected: PASS（4 passed）

- [x] **Step 5: Verify full suite still green**

Run: `uv run pytest -q`
Expected: 103 passed（99 + 4 new）

- [x] **Step 6: Commit**

```bash
git add app/schemas/order.py tests/test_schemas_admin_order.py
git commit -m "feat(backend): admin order schemas"
```

---

## Task 2: order_repo.list_filtered

**Files:**
- Modify: `app/repositories/order_repo.py`
- Modify: `tests/test_order_repo.py`（append 6 new tests）

- [x] **Step 1: Extend `tests/test_order_repo.py`**

First, update the existing import at the top of the file from:
```python
from datetime import date
```
to:
```python
from datetime import date, timedelta
```

Then append the following test functions at the **end** of the file:

```python


async def test_list_filtered_no_filter_returns_all(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-LF01"))
    await order_repo.add(db_session, _make_order("MM-LF02"))
    await db_session.flush()
    total, orders = await order_repo.list_filtered(db_session, page=1, page_size=20)
    assert total >= 2
    nos = {o.order_no for o in orders}
    assert {"MM-LF01", "MM-LF02"} <= nos


async def test_list_filtered_by_status(db_session: AsyncSession):
    # _make_order 預設 status="pending_payment"
    await order_repo.add(db_session, _make_order("MM-ST01"))
    pending = Order(
        order_no="MM-ST02", status="pending",
        customer_name="B", customer_phone="0911000000", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="cod", note=None,
        subtotal=880, shipping_fee=0, cod_fee=30, total=910,
    )
    await order_repo.add(db_session, pending)
    await db_session.flush()
    total, results = await order_repo.list_filtered(db_session, status="pending", page=1, page_size=20)
    nos = {o.order_no for o in results}
    assert "MM-ST02" in nos
    assert "MM-ST01" not in nos
    assert all(o.status == "pending" for o in results)


async def test_list_filtered_by_q_customer_name(db_session: AsyncSession):
    named = Order(
        order_no="MM-Q01", status="pending",
        customer_name="林美麗", customer_phone="0933333333", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="cod", note=None,
        subtotal=880, shipping_fee=0, cod_fee=30, total=910,
    )
    await order_repo.add(db_session, named)
    await db_session.flush()
    _, results = await order_repo.list_filtered(db_session, q="林美麗", page=1, page_size=20)
    assert any(o.order_no == "MM-Q01" for o in results)


async def test_list_filtered_by_order_no(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-EXACT1"))
    await order_repo.add(db_session, _make_order("MM-EXACT2"))
    await db_session.flush()
    total, results = await order_repo.list_filtered(db_session, order_no="MM-EXACT1", page=1, page_size=20)
    assert total == 1
    assert results[0].order_no == "MM-EXACT1"


async def test_list_filtered_by_date(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    today = date.today()
    _, results = await order_repo.list_filtered(db_session, date_from=today, page=1, page_size=20)
    assert any(o.order_no == "MM-DT01" for o in results)
    yesterday = today - timedelta(days=1)
    _, old_results = await order_repo.list_filtered(db_session, date_to=yesterday, page=1, page_size=20)
    assert not any(o.order_no == "MM-DT01" for o in old_results)


async def test_list_filtered_pagination(db_session: AsyncSession):
    for i in range(3):
        await order_repo.add(db_session, _make_order(f"MM-PG{i:02d}"))
    await db_session.flush()
    total, page1 = await order_repo.list_filtered(db_session, page=1, page_size=2)
    assert total >= 3
    assert len(page1) == 2
    _, page2 = await order_repo.list_filtered(db_session, page=2, page_size=2)
    assert len(page2) >= 1
    assert {o.order_no for o in page1}.isdisjoint({o.order_no for o in page2})
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_order_repo.py -v`
Expected: FAIL — `AttributeError: module 'app.repositories.order_repo' has no attribute 'list_filtered'`

- [x] **Step 3: Implement `list_filtered` in `app/repositories/order_repo.py`**

Full updated file:

```python
from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def add(session: AsyncSession, order: Order) -> Order:
    session.add(order)
    await session.flush()
    return order


async def get_by_order_no(session: AsyncSession, order_no: str) -> Order | None:
    result = await session.execute(select(Order).where(Order.order_no == order_no))
    return result.scalar_one_or_none()


async def list_filtered(
    session: AsyncSession,
    *,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    order_no: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Order]]:
    count_stmt = select(func.count()).select_from(Order)
    list_stmt = select(Order)

    if status is not None:
        count_stmt = count_stmt.where(Order.status == status)
        list_stmt = list_stmt.where(Order.status == status)
    if date_from is not None:
        count_stmt = count_stmt.where(Order.created_at >= date_from)
        list_stmt = list_stmt.where(Order.created_at >= date_from)
    if date_to is not None:
        boundary = date_to + timedelta(days=1)
        count_stmt = count_stmt.where(Order.created_at < boundary)
        list_stmt = list_stmt.where(Order.created_at < boundary)
    if q is not None:
        pattern = f"%{q}%"
        condition = or_(
            Order.customer_name.ilike(pattern),
            Order.customer_phone.ilike(pattern),
        )
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)
    if order_no is not None:
        count_stmt = count_stmt.where(Order.order_no == order_no)
        list_stmt = list_stmt.where(Order.order_no == order_no)

    total: int = (await session.execute(count_stmt)).scalar_one()
    rows = await session.execute(
        list_stmt.order_by(Order.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return total, list(rows.scalars().all())
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_order_repo.py -v`
Expected: PASS（10 passed；既有 4 + 新 6）

- [x] **Step 5: Verify full suite + lint + types**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 109 passed；ruff clean；mypy Success

- [x] **Step 6: Commit**

```bash
git add app/repositories/order_repo.py tests/test_order_repo.py
git commit -m "feat(backend): order_repo.list_filtered (status/date/q/order_no/page)"
```

---

## Task 3: admin_order_service

**Files:**
- Create: `app/services/admin_order_service.py`
- Create: `tests/test_admin_order_service.py`

- [x] **Step 1: Write the failing test** — `tests/test_admin_order_service.py`

```python
from datetime import date as date_type

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStatusTransition, NotFoundError
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import order_repo
from app.services import admin_order_service


def _make_order(
    order_no: str,
    *,
    status: str = "pending",
    customer_name: str = "王小明",
    customer_phone: str = "0912345678",
) -> Order:
    return Order(
        order_no=order_no,
        status=status,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=None,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date_type(2026, 10, 1),
        delivery_window="any",
        payment_method="cod",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=30,
        total=910,
    )


async def test_list_orders_empty(db_session: AsyncSession):
    resp = await admin_order_service.list_orders(db_session)
    assert resp.total == 0
    assert resp.items == []
    assert resp.page == 1
    assert resp.page_size == 20


async def test_list_orders_returns_all(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-LS01"))
    await order_repo.add(db_session, _make_order("MM-LS02"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session)
    assert resp.total == 2
    assert len(resp.items) == 2


async def test_list_orders_filter_by_status(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ST01", status="pending"))
    await order_repo.add(db_session, _make_order("MM-ST02", status="confirmed"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, status="pending")
    nos = {item.order_no for item in resp.items}
    assert "MM-ST01" in nos
    assert "MM-ST02" not in nos
    assert all(item.status == "pending" for item in resp.items)


async def test_list_orders_filter_by_q(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-Q01", customer_name="林美麗"))
    await order_repo.add(db_session, _make_order("MM-Q02", customer_name="陳大明"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, q="林美麗")
    assert resp.total == 1
    assert resp.items[0].order_no == "MM-Q01"


async def test_list_orders_pagination(db_session: AsyncSession):
    for i in range(3):
        await order_repo.add(db_session, _make_order(f"MM-PG{i:02d}"))
    await db_session.flush()
    resp = await admin_order_service.list_orders(db_session, page=1, page_size=2)
    assert resp.total == 3
    assert len(resp.items) == 2


async def test_get_order_detail(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    detail = await admin_order_service.get_order_detail(db_session, "MM-DT01")
    assert detail.order_no == "MM-DT01"
    assert detail.ship_city == "台北市"
    assert detail.customer_name == "王小明"
    assert isinstance(detail.items, list)


async def test_get_order_detail_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.get_order_detail(db_session, "MM-GHOST")


async def test_change_status_valid_transition(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR01", status="pending"))
    await db_session.flush()
    result = await admin_order_service.change_order_status(db_session, "MM-TR01", "confirmed")
    assert result.status == "confirmed"


async def test_change_status_invalid_transition_raises(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-TR02", status="shipping"))
    await db_session.flush()
    with pytest.raises(InvalidStatusTransition):
        await admin_order_service.change_order_status(db_session, "MM-TR02", "cancelled")


async def test_change_status_order_not_found(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await admin_order_service.change_order_status(db_session, "MM-GHOST", "confirmed")


async def test_cancel_restores_stock(db_session: AsyncSession):
    product = Product(
        slug="kanro2", name="甘露梨", description="d", image="i", season="s"
    )
    db_session.add(product)
    await db_session.flush()

    spec = ProductSpec(
        product_id=product.id,
        label="A",
        qty_text="q",
        price=880,
        stock_qty=5,
        sort_order=1,
    )
    db_session.add(spec)
    await db_session.flush()

    order = _make_order("MM-CANCEL1", status="confirmed")
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        spec_id=spec.id,
        product_name="甘露梨",
        spec_label="A",
        unit_price=880,
        qty=2,
        line_total=1760,
    )
    db_session.add(item)
    await db_session.flush()

    await admin_order_service.change_order_status(db_session, "MM-CANCEL1", "cancelled")
    await db_session.refresh(spec)
    assert spec.stock_qty == 7  # 5 + 2


async def test_cancel_with_null_spec_id_skips_silently(db_session: AsyncSession):
    order = _make_order("MM-CANCEL2", status="confirmed")
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=99999,
        spec_id=None,
        product_name="已下架商品",
        spec_label="A",
        unit_price=880,
        qty=1,
        line_total=880,
    )
    db_session.add(item)
    await db_session.flush()

    result = await admin_order_service.change_order_status(db_session, "MM-CANCEL2", "cancelled")
    assert result.status == "cancelled"
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_admin_order_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.admin_order_service'`

- [x] **Step 3: Create `app/services/admin_order_service.py`**

```python
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
                spec = await spec_repo.get_by_id(session, item.spec_id)
                if spec is not None:
                    spec.stock_qty += item.qty
    order.status = new_status
    await session.commit()
    await session.refresh(order)
    return _to_admin_order_read(order)
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_admin_order_service.py -v`
Expected: PASS（12 passed）

- [x] **Step 5: Verify suite + lint + types**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 121 passed；ruff clean；mypy Success

- [x] **Step 6: Commit**

```bash
git add app/services/admin_order_service.py tests/test_admin_order_service.py
git commit -m "feat(backend): admin_order_service (list/detail/change_status + stock restore)"
```

---

## Task 4: Admin Orders Route

**Files:**
- Create: `app/api/routes/admin_orders.py`
- Modify: `app/main.py`
- Create: `tests/test_admin_orders_api.py`

- [x] **Step 1: Write the failing test** — `tests/test_admin_orders_api.py`

```python
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.repositories import admin_repo, order_repo


def _make_order(order_no: str, *, status: str = "pending") -> Order:
    return Order(
        order_no=order_no,
        status=status,
        customer_name="王小明",
        customer_phone="0912345678",
        customer_email=None,
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="重慶南路1號",
        preferred_date=date(2026, 10, 1),
        delivery_window="any",
        payment_method="cod",
        note=None,
        subtotal=880,
        shipping_fee=0,
        cod_fee=30,
        total=910,
    )


async def _auth_header(session: AsyncSession) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(
            username="miaomama", hashed_password=hash_password("pw"), is_active=True
        ),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def test_admin_orders_require_auth(client: AsyncClient):
    assert (await client.get("/api/admin/orders")).status_code == 401


async def test_list_orders_returns_response_structure(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-API01"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert {"total", "page", "page_size", "items"} <= set(body)
    assert body["total"] >= 1
    assert body["items"][0]["order_no"] == "MM-API01"


async def test_list_orders_filter_by_status(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-API02", status="pending"))
    await order_repo.add(db_session, _make_order("MM-API03", status="confirmed"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders?status=pending", headers=headers)
    assert resp.status_code == 200
    nos = [item["order_no"] for item in resp.json()["items"]]
    assert "MM-API02" in nos
    assert "MM-API03" not in nos


async def test_get_order_detail(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-DT01"))
    await db_session.flush()
    resp = await client.get("/api/admin/orders/MM-DT01", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_no"] == "MM-DT01"
    assert "ship_city" in body
    assert "items" in body


async def test_get_order_detail_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    resp = await client.get("/api/admin/orders/MM-GHOST", headers=headers)
    assert resp.status_code == 404


async def test_change_status_valid_transition(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-CH01", status="pending"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-CH01/status",
        json={"status": "confirmed"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


async def test_change_status_invalid_transition(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await order_repo.add(db_session, _make_order("MM-CH02", status="shipping"))
    await db_session.flush()
    resp = await client.patch(
        "/api/admin/orders/MM-CH02/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "INVALID_STATUS_TRANSITION"


async def test_change_status_order_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    resp = await client.patch(
        "/api/admin/orders/MM-GHOST/status",
        json={"status": "confirmed"},
        headers=headers,
    )
    assert resp.status_code == 404
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_admin_orders_api.py -v`
Expected: FAIL — 401 on all routes except the auth check（routes 尚未 include）

- [x] **Step 3: Create `app/api/routes/admin_orders.py`**

```python
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.schemas.order import AdminOrderListResponse, AdminOrderRead, OrderStatusUpdate
from app.services import admin_order_service

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-orders"],
    dependencies=[Depends(get_current_admin)],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/orders", response_model=AdminOrderListResponse)
async def list_orders(
    session: SessionDep,
    status: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    q: str | None = Query(default=None),
    order_no: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AdminOrderListResponse:
    return await admin_order_service.list_orders(
        session,
        status=status,
        date_from=date_from,
        date_to=date_to,
        q=q,
        order_no=order_no,
        page=page,
        page_size=page_size,
    )


@router.get("/orders/{order_no}", response_model=AdminOrderRead)
async def get_order(order_no: str, session: SessionDep) -> AdminOrderRead:
    return await admin_order_service.get_order_detail(session, order_no)


@router.patch("/orders/{order_no}/status", response_model=AdminOrderRead)
async def change_status(
    order_no: str, data: OrderStatusUpdate, session: SessionDep
) -> AdminOrderRead:
    return await admin_order_service.change_order_status(session, order_no, data.status)
```

- [x] **Step 4: Wire router into `app/main.py`**

Extend the import line from:
```python
from app.api.routes import admin_auth, admin_products, orders, products
```
to:
```python
from app.api.routes import admin_auth, admin_orders, admin_products, orders, products
```

Inside `create_app()`, add alongside the other `include_router` calls:
```python
    app.include_router(admin_orders.router)
```

- [x] **Step 5: Run tests + full suite**

Run: `uv run pytest tests/test_admin_orders_api.py -v`
Expected: PASS（8 passed）

Run: `uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 129 passed；ruff clean；mypy Success

- [x] **Step 6: Commit**

```bash
git add app/api/routes/admin_orders.py app/main.py tests/test_admin_orders_api.py
git commit -m "feat(backend): admin order routes (list/detail/change-status)"
```

---

## Definition of Done (Phase 4b)

- [x] `cd backend && uv run pytest -q` → 129 passed（99 既有 + 4 schemas + 6 repo + 12 service + 8 api）
- [x] `cd backend && uv run ruff check .` → clean
- [x] `cd backend && uv run mypy app` → Success
- [x] `GET /api/admin/orders` 需 JWT；支援 `status`、`date_from`/`date_to`、`q`、`order_no`、`page`/`page_size` 篩選；回 `AdminOrderListResponse`（含 total/page）
- [x] `GET /api/admin/orders/{order_no}` 回完整 `AdminOrderRead`（含 items + 所有物流/金額欄位）；找不到 → 404
- [x] `PATCH /api/admin/orders/{order_no}/status` 合法轉移 → 200 + 新狀態；非法 → 409 `INVALID_STATUS_TRANSITION`；取消 → 自動回補 `spec.stock_qty`
- [x] `shipping` / `delivered` 轉 `cancelled` → 409（不可取消）
- [x] `order_service.py`（Phase 4a create_order）未被修改
- [x] 全部任務已提交；plan checkboxes 已勾選
