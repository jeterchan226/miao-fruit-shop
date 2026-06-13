# Phase 4a:公開下單(Public Order Creation)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. When a task is fully done (spec + quality review passed), also tick its checkboxes here.

**Goal:** 實作公開端點 `POST /api/orders`:伺服器權威重算金額、價格確認、行鎖驗/扣庫存、產生 `order_no` 並建立訂單。

**Architecture:** 沿用現有三層(routes → services → repositories + core)。新增 `orders`/`order_items` 模型(明細快照)與第三個 Alembic 遷移。`order_service.create_order` 在單一交易內完成:`SELECT ... FOR UPDATE` 鎖規格 → 重算金額 → 比對 `expected_total`(不符拋 `PriceChangedError`)→ 驗庫存(不足拋 `InsufficientStockError`)→ 扣庫存、產 `order_no`、建單、commit。金額常數集中於 `core/constants.py`,金額/狀態/order_no 為可單測的純函式。

**Tech Stack:** FastAPI、SQLAlchemy 2.0 async(`Mapped`/`mapped_column`、selectin relationship、`with_for_update`)、Alembic async、Pydantic v2、PostgreSQL、pytest + httpx AsyncClient。

**規範對齊(來自既有程式碼):**
- 領域例外繼承 `app/core/exceptions.py` 的 `AppError`(帶 `code` / `status_code`),由 `app/api/errors.py` 對映 HTTP。
- repo 函式 `add` 只 `flush` 不 `commit`;交易在 service 內 commit。
- route 用 `SessionDep = Annotated[AsyncSession, Depends(get_session)]`。
- 測試以 `db_session`(savepoint 隔離,測試結束 rollback)與 `client`(覆寫 `get_session`)兩個 fixture。
- **測試函式不加 `-> None` 註記**(專案慣例;`mypy app` 不掃 tests)。
- 金額一律整數 NT$。

---

## 檔案結構

新增:
- `app/models/order.py` — `Order` ORM model。
- `app/models/order_item.py` — `OrderItem` ORM model(明細快照)。
- `app/core/constants.py` — 金額常數。
- `app/schemas/order.py` — `OrderCreate`(含巢狀 customer/shipping/items)、`OrderRead`、`PriceChangedResponse`。
- `app/repositories/order_repo.py` — `add`、`get_by_order_no`。
- `app/services/order_service.py` — 純函式(`compute_amounts`/`initial_status`/`_new_order_no`)+ `create_order`。
- `app/api/routes/orders.py` — `POST /api/orders`。
- `alembic/versions/<rev>_create_orders_and_order_items.py` — autogenerate。
- 測試:`tests/test_order_amounts.py`、`tests/test_schemas_order.py`、`tests/test_order_repo.py`、`tests/test_order_service.py`、`tests/test_orders_api.py`。

修改:
- `app/models/__init__.py` — 匯出 `Order`、`OrderItem`。
- `app/core/exceptions.py` — 新增 `PriceChangedError`。
- `app/api/errors.py` — 新增 `PriceChangedError` 專屬 handler(body 含金額明細)。
- `app/repositories/spec_repo.py` — 新增 `get_for_update`。
- `app/main.py` — include `orders` router。

---

## Task 1: Order / OrderItem models

**Files:**
- Create: `backend/app/models/order.py`
- Create: `backend/app/models/order_item.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_order_models.py`

- [x] **Step 1: Write the failing test** — `backend/tests/test_order_models.py`

```python
from app.core.database import Base
from app.models import Order, OrderItem


def test_order_tables_registered_on_metadata():
    tables = set(Base.metadata.tables)
    assert "orders" in tables
    assert "order_items" in tables


def test_order_has_expected_columns():
    cols = set(Order.__table__.columns.keys())
    assert {
        "id", "order_no", "status", "customer_name", "customer_phone",
        "customer_email", "ship_zipcode", "ship_city", "ship_district",
        "ship_street", "preferred_date", "delivery_window", "payment_method",
        "note", "subtotal", "shipping_fee", "cod_fee", "total",
        "created_at", "updated_at",
    } <= cols


def test_order_item_has_snapshot_columns():
    cols = set(OrderItem.__table__.columns.keys())
    assert {
        "id", "order_id", "product_id", "spec_id", "product_name",
        "spec_label", "unit_price", "qty", "line_total",
    } <= cols
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_order_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Order' from 'app.models'`.

- [x] **Step 3: Write `backend/app/models/order.py`**

```python
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order_item import OrderItem


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[str] = mapped_column()
    customer_name: Mapped[str] = mapped_column()
    customer_phone: Mapped[str] = mapped_column()
    customer_email: Mapped[str | None] = mapped_column(default=None)
    ship_zipcode: Mapped[str] = mapped_column()
    ship_city: Mapped[str] = mapped_column()
    ship_district: Mapped[str] = mapped_column()
    ship_street: Mapped[str] = mapped_column()
    preferred_date: Mapped[date] = mapped_column()
    delivery_window: Mapped[str] = mapped_column()
    payment_method: Mapped[str] = mapped_column()
    note: Mapped[str | None] = mapped_column(Text, default=None)
    subtotal: Mapped[int] = mapped_column()
    shipping_fee: Mapped[int] = mapped_column()
    cod_fee: Mapped[int] = mapped_column()
    total: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="OrderItem.id",
        cascade="all, delete-orphan",
    )
```

- [x] **Step 4: Write `backend/app/models/order_item.py`**

```python
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column()
    spec_id: Mapped[int | None] = mapped_column(default=None)
    product_name: Mapped[str] = mapped_column()
    spec_label: Mapped[str] = mapped_column()
    unit_price: Mapped[int] = mapped_column()
    qty: Mapped[int] = mapped_column()
    line_total: Mapped[int] = mapped_column()

    order: Mapped["Order"] = relationship(back_populates="items")
```

- [x] **Step 5: Update `backend/app/models/__init__.py`**

```python
from app.models.admin_user import AdminUser
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_spec import ProductSpec

__all__ = ["AdminUser", "Order", "OrderItem", "Product", "ProductSpec"]
```

- [x] **Step 6: Run test + verify lint/types/suite**

Run: `cd backend && uv run pytest tests/test_order_models.py -v && uv run ruff check . && uv run mypy app`
Expected: 3 passed; ruff clean; mypy Success.

- [x] **Step 7: Commit**

```bash
cd backend && git add app/models/order.py app/models/order_item.py app/models/__init__.py tests/test_order_models.py
git commit -m "feat(backend): Order and OrderItem models"
```

---

## Task 2: Alembic migration (orders + order_items)

**Files:**
- Create: `backend/alembic/versions/<rev>_create_orders_and_order_items.py` (autogenerate)

- [x] **Step 1: Autogenerate**

Run: `cd backend && uv run alembic revision --autogenerate -m "create orders and order_items"`
Expected: 產生新檔於 `alembic/versions/`。

- [x] **Step 2: Sanity-check the generated file**

開啟產生的檔案,確認:
- `down_revision = "16c86ea7cbda"`(接在 products 遷移之後)。
- `upgrade()` 內 `op.create_table("orders", ...)` 與 `op.create_table("order_items", ...)` 皆存在。
- `orders.order_no` 有 unique 約束與 index;`order_items.order_id` 有 FK→`orders.id` 與 index。
- `downgrade()` 對應 `op.drop_table("order_items")` 與 `op.drop_table("orders")`(順序:先 items 後 orders)。
- 不應出現對 `products` / `product_specs` / `admin_users` 的非預期變更(若有,代表模型漂移,需先釐清)。

- [x] **Step 3: Apply**

Run: `cd backend && uv run alembic upgrade head`
Expected: `Running upgrade 16c86ea7cbda -> <rev>, create orders and order_items`。

- [x] **Step 4: Verify head**

Run: `cd backend && uv run alembic current`
Expected: 顯示新 `<rev> (head)`。

- [x] **Step 5: Suite still green**

Run: `cd backend && uv run pytest -q`
Expected: 全數通過(測試 DB 由 `Base.metadata.create_all` 建立,不受遷移影響)。

- [x] **Step 6: Commit**

```bash
cd backend && git add alembic/versions/
git commit -m "feat(backend): migration create orders and order_items"
```

---

## Task 3: 金額/狀態/order_no 純函式 + PriceChangedError + 常數

**Files:**
- Create: `backend/app/core/constants.py`
- Modify: `backend/app/core/exceptions.py`
- Create: `backend/app/services/order_service.py`(本任務只放純函式;Task 6 再加 `create_order`)
- Test: `backend/tests/test_order_amounts.py`

- [x] **Step 1: Write the failing test** — `backend/tests/test_order_amounts.py`

```python
from app.services.order_service import (
    Amounts,
    _new_order_no,
    compute_amounts,
    initial_status,
)

ORDER_NO_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def test_shipping_free_at_threshold():
    a = compute_amounts(5000, "linepay")
    assert a == Amounts(subtotal=5000, shipping_fee=0, cod_fee=0, total=5000)


def test_shipping_charged_below_threshold():
    a = compute_amounts(4999, "linepay")
    assert a == Amounts(subtotal=4999, shipping_fee=150, cod_fee=0, total=5149)


def test_cod_fee_added_for_cod():
    a = compute_amounts(1000, "cod")
    assert a == Amounts(subtotal=1000, shipping_fee=150, cod_fee=30, total=1180)


def test_cod_fee_zero_for_non_cod():
    a = compute_amounts(1000, "atm")
    assert a.cod_fee == 0


def test_initial_status_cod_is_pending():
    assert initial_status("cod") == "pending"


def test_initial_status_prepaid_is_pending_payment():
    assert initial_status("linepay") == "pending_payment"
    assert initial_status("card") == "pending_payment"
    assert initial_status("atm") == "pending_payment"


def test_order_no_format():
    no = _new_order_no()
    assert no.startswith("MM-")
    assert len(no) == 9
    assert all(c in ORDER_NO_ALPHABET for c in no[3:])
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_order_amounts.py -v`
Expected: FAIL — `ModuleNotFoundError`/`ImportError` (order_service 尚未建立)。

- [x] **Step 3: Write `backend/app/core/constants.py`**

```python
# 金額規則常數(與前端 frontend/src/Cart.jsx 對齊)。金額一律整數 NT$。
FREE_SHIPPING_THRESHOLD = 5000  # subtotal 達此值(含)以上免運
SHIPPING_FEE = 150
COD_FEE = 30
```

- [x] **Step 4: Append `PriceChangedError` to `backend/app/core/exceptions.py`**

在檔案末端新增(沿用既有 `AppError` 樣式):

```python
class PriceChangedError(AppError):
    code = "PRICE_CHANGED"
    status_code = 409

    def __init__(
        self,
        detail: str,
        *,
        subtotal: int,
        shipping_fee: int,
        cod_fee: int,
        total: int,
    ) -> None:
        super().__init__(detail)
        self.subtotal = subtotal
        self.shipping_fee = shipping_fee
        self.cod_fee = cod_fee
        self.total = total
```

- [x] **Step 5: Write `backend/app/services/order_service.py`**(本任務僅純函式)

```python
import secrets
from typing import NamedTuple

from app.core.constants import COD_FEE, FREE_SHIPPING_THRESHOLD, SHIPPING_FEE

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
    return "pending" if payment_method == "cod" else "pending_payment"


def _new_order_no() -> str:
    suffix = "".join(secrets.choice(ORDER_NO_ALPHABET) for _ in range(6))
    return f"MM-{suffix}"
```

- [x] **Step 6: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_order_amounts.py -v && uv run ruff check . && uv run mypy app`
Expected: 8 passed;ruff clean;mypy Success。

- [x] **Step 7: Commit**

```bash
cd backend && git add app/core/constants.py app/core/exceptions.py app/services/order_service.py tests/test_order_amounts.py
git commit -m "feat(backend): order amounts/status/order_no helpers + PriceChangedError"
```

---

## Task 4: Schemas(`schemas/order.py`)

**Files:**
- Create: `backend/app/schemas/order.py`
- Test: `backend/tests/test_schemas_order.py`

- [x] **Step 1: Write the failing test** — `backend/tests/test_schemas_order.py`

```python
import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreate


def _valid_payload(**overrides):
    payload = {
        "customer": {"name": "王小明", "phone": "0912345678", "email": None},
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "重慶南路一段 122 號", "preferred_date": "2026-10-12",
            "delivery_window": "am",
        },
        "items": [{"spec_id": 1, "qty": 2}],
        "payment_method": "linepay",
        "note": None,
        "expected_total": 3910,
    }
    payload.update(overrides)
    return payload


def test_valid_payload_parses():
    order = OrderCreate.model_validate(_valid_payload())
    assert order.items[0].spec_id == 1
    assert order.items[0].qty == 2
    assert order.shipping.delivery_window == "am"
    assert order.expected_total == 3910


def test_empty_items_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(items=[]))


def test_qty_below_one_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(items=[{"spec_id": 1, "qty": 0}]))


def test_bad_delivery_window_rejected():
    bad = _valid_payload()
    bad["shipping"]["delivery_window"] = "midnight"
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(bad)


def test_bad_payment_method_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(payment_method="bitcoin"))


def test_extra_top_level_field_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(hacker_price=1))
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_schemas_order.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.schemas.order'`。

- [x] **Step 3: Write `backend/app/schemas/order.py`**

```python
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None


class ShippingCreate(BaseModel):
    zipcode: str
    city: str
    district: str
    street: str
    preferred_date: date
    delivery_window: Literal["any", "am", "pm"]


class OrderItemCreate(BaseModel):
    spec_id: int
    qty: int = Field(ge=1)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: CustomerCreate
    shipping: ShippingCreate
    items: list[OrderItemCreate] = Field(min_length=1)
    payment_method: Literal["linepay", "card", "atm", "cod"]
    note: str | None = None
    expected_total: int = Field(ge=0)


class OrderItemRead(BaseModel):
    product_name: str
    spec_label: str
    unit_price: int
    qty: int
    line_total: int


class OrderRead(BaseModel):
    order_no: str
    status: str
    items: list[OrderItemRead]
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int
    created_at: datetime


class PriceChangedResponse(BaseModel):
    """409 PRICE_CHANGED 的回應體(供文件/前端參考)。"""

    detail: str
    code: str = "PRICE_CHANGED"
    subtotal: int
    shipping_fee: int
    cod_fee: int
    total: int
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_schemas_order.py -v && uv run ruff check . && uv run mypy app`
Expected: 6 passed;ruff clean;mypy Success。

- [x] **Step 5: Commit**

```bash
cd backend && git add app/schemas/order.py tests/test_schemas_order.py
git commit -m "feat(backend): order schemas"
```

---

## Task 5: Repositories(order_repo + spec_repo.get_for_update)

**Files:**
- Create: `backend/app/repositories/order_repo.py`
- Modify: `backend/app/repositories/spec_repo.py`
- Test: `backend/tests/test_order_repo.py`

- [x] **Step 1: Write the failing test** — `backend/tests/test_order_repo.py`

```python
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import order_repo, product_repo, spec_repo


def _make_order(order_no: str) -> Order:
    return Order(
        order_no=order_no, status="pending_payment",
        customer_name="A", customer_phone="0912345678", customer_email=None,
        ship_zipcode="100", ship_city="台北市", ship_district="中正區",
        ship_street="x", preferred_date=date(2026, 10, 12),
        delivery_window="any", payment_method="linepay", note=None,
        subtotal=1880, shipping_fee=150, cod_fee=0, total=2030,
    )


async def test_add_and_get_by_order_no(db_session: AsyncSession):
    await order_repo.add(db_session, _make_order("MM-ABC234"))
    await db_session.flush()
    fetched = await order_repo.get_by_order_no(db_session, "MM-ABC234")
    assert fetched is not None
    assert fetched.total == 2030


async def test_get_by_order_no_missing_returns_none(db_session: AsyncSession):
    assert await order_repo.get_by_order_no(db_session, "MM-NOPE99") is None


async def test_spec_get_for_update_returns_spec(db_session: AsyncSession):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    spec_id = product.specs[0].id
    locked = await spec_repo.get_for_update(db_session, spec_id)
    assert locked is not None
    assert locked.id == spec_id
    assert locked.product.name == "甘露梨"


async def test_spec_get_for_update_missing_returns_none(db_session: AsyncSession):
    assert await spec_repo.get_for_update(db_session, 999999) is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_order_repo.py -v`
Expected: FAIL — `ImportError: cannot import name 'order_repo'` 或 `AttributeError: ... 'get_for_update'`。

- [x] **Step 3: Write `backend/app/repositories/order_repo.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def add(session: AsyncSession, order: Order) -> Order:
    session.add(order)
    await session.flush()
    return order


async def get_by_order_no(session: AsyncSession, order_no: str) -> Order | None:
    result = await session.execute(select(Order).where(Order.order_no == order_no))
    return result.scalar_one_or_none()
```

- [x] **Step 4: Add `get_for_update` to `backend/app/repositories/spec_repo.py`**

更新整個檔案(在既有 `get_by_id` / `add` 之外新增 `get_for_update`,並補上 `select` / `selectinload` import):

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product_spec import ProductSpec


async def get_by_id(session: AsyncSession, spec_id: int) -> ProductSpec | None:
    return await session.get(ProductSpec, spec_id)


async def get_for_update(session: AsyncSession, spec_id: int) -> ProductSpec | None:
    """以列鎖(SELECT ... FOR UPDATE)讀取規格,並一併載入所屬商品(供快照品名)。"""
    result = await session.execute(
        select(ProductSpec)
        .where(ProductSpec.id == spec_id)
        .with_for_update()
        .options(selectinload(ProductSpec.product))
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, spec: ProductSpec) -> ProductSpec:
    session.add(spec)
    await session.flush()
    return spec
```

- [x] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_order_repo.py -v && uv run ruff check . && uv run mypy app`
Expected: 4 passed;ruff clean;mypy Success。

- [x] **Step 6: Commit**

```bash
cd backend && git add app/repositories/order_repo.py app/repositories/spec_repo.py tests/test_order_repo.py
git commit -m "feat(backend): order repo + spec get_for_update"
```

---

## Task 6: order_service.create_order

**Files:**
- Modify: `backend/app/services/order_service.py`(在 Task 3 純函式之後 append)
- Test: `backend/tests/test_order_service.py`

- [x] **Step 1: Write the failing test** — `backend/tests/test_order_service.py`

```python
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
    # subtotal 1880 → 運費 150(未達免運)→ total 2030
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
    # 庫存已扣
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 9


async def test_create_order_cod_status_and_fee(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=6000, stock=5)
    # subtotal 6000 → 免運 0;cod 手續費 30 → total 6030
    result = await order_service.create_order(
        db_session, _payload(spec.id, 1, payment="cod", expected_total=6030)
    )
    assert result.status == "pending"
    assert result.shipping_fee == 0
    assert result.cod_fee == 30
    assert result.total == 6030


async def test_price_changed_blocks_and_keeps_stock(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    with pytest.raises(PriceChangedError) as exc:
        await order_service.create_order(
            db_session, _payload(spec.id, 1, expected_total=9999)
        )
    # 例外帶權威新明細
    assert exc.value.total == 2030
    # 未扣庫存、未建單
    refreshed = await db_session.get(ProductSpec, spec.id)
    assert refreshed.stock_qty == 10
    assert await _order_count(db_session) == 0


async def test_insufficient_stock_blocks_and_keeps_stock(db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=2)
    # qty 5 > stock 2;subtotal 9400 → 免運 → total 9400
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_order_service.py -v`
Expected: FAIL — `AttributeError: module 'app.services.order_service' has no attribute 'create_order'`。

- [x] **Step 3: Append to `backend/app/services/order_service.py`**

在 Task 3 的純函式之後新增 import 與 `create_order` / `_to_order_read`。完成後檔案頂端的 import 區塊應為:

```python
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
```

在檔案末端(`_new_order_no` 之後)新增:

```python
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
    for spec, qty in locked:
        spec.stock_qty -= qty

    order = Order(
        order_no=await _generate_unique_order_no(session),
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
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_order_service.py -v`
Expected: 6 passed。

- [x] **Step 5: Verify suite + lint + types**

Run: `cd backend && uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: 全綠;mypy Success。

- [x] **Step 6: Commit**

```bash
cd backend && git add app/services/order_service.py tests/test_order_service.py
git commit -m "feat(backend): order_service.create_order (lock/recompute/confirm/decrement)"
```

---

## Task 7: 端點 `POST /api/orders` + error handler + 接線

**Files:**
- Modify: `backend/app/api/errors.py`
- Create: `backend/app/api/routes/orders.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_orders_api.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/test_orders_api.py`

```python
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo


async def _seed_spec(db_session, *, price=1880, stock=10):
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="5 台斤家庭箱", qty_text="q", price=price,
                    stock_qty=stock, sort_order=1)
    ]
    await product_repo.add(db_session, product)
    await db_session.flush()
    return product.specs[0]


def _body(spec_id, qty, *, payment="linepay", expected_total):
    return {
        "customer": {"name": "王小明", "phone": "0912345678", "email": None},
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "x", "preferred_date": "2026-10-12", "delivery_window": "any",
        },
        "items": [{"spec_id": spec_id, "qty": qty}],
        "payment_method": payment,
        "note": None,
        "expected_total": expected_total,
    }


async def test_create_order_201(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    resp = await client.post("/api/orders", json=_body(spec.id, 1, expected_total=2030))
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_no"].startswith("MM-")
    assert data["status"] == "pending_payment"
    assert data["total"] == 2030
    assert data["items"][0]["unit_price"] == 1880
    # 回應不揭露庫存數量
    assert "stock_qty" not in str(data)


async def test_create_order_price_changed_409(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=10)
    resp = await client.post("/api/orders", json=_body(spec.id, 1, expected_total=9999))
    assert resp.status_code == 409
    data = resp.json()
    assert data["code"] == "PRICE_CHANGED"
    assert data["total"] == 2030  # 回權威新明細


async def test_create_order_insufficient_stock_409(client: AsyncClient, db_session: AsyncSession):
    spec = await _seed_spec(db_session, price=1880, stock=2)
    resp = await client.post("/api/orders", json=_body(spec.id, 5, expected_total=9400))
    assert resp.status_code == 409
    assert resp.json()["code"] == "INSUFFICIENT_STOCK"


async def test_create_order_unknown_spec_404(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post("/api/orders", json=_body(999999, 1, expected_total=0))
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


async def test_create_order_validation_422(client: AsyncClient, db_session: AsyncSession):
    # 空 items
    resp = await client.post("/api/orders", json=_body(1, 1, expected_total=0) | {"items": []})
    assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_orders_api.py -v`
Expected: FAIL — 404(路由不存在)或 import 錯誤。

- [ ] **Step 3: Add `PriceChangedError` handler to `backend/app/api/errors.py`**

更新整個檔案(在既有 `AppError` handler 之外,新增更特定的 `PriceChangedError` handler,使其 body 帶金額明細):

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError, PriceChangedError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PriceChangedError)
    async def _handle_price_changed(
        _request: Request, exc: PriceChangedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
                "subtotal": exc.subtotal,
                "shipping_fee": exc.shipping_fee,
                "cod_fee": exc.cod_fee,
                "total": exc.total,
            },
        )

    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )
```

> 註:Starlette 依例外的 MRO 取最特定的 handler,`PriceChangedError` 會優先於 `AppError` 被選用。

- [ ] **Step 4: Write `backend/app/api/routes/orders.py`**

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service

router = APIRouter(prefix="/api", tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(data: OrderCreate, session: SessionDep) -> OrderRead:
    return await order_service.create_order(session, data)
```

- [ ] **Step 5: Wire into `backend/app/main.py`**

更新 router import 與 include:

```python
from app.api.routes import admin_auth, admin_products, orders, products
```

並在既有 `app.include_router(...)` 區塊新增:

```python
    app.include_router(orders.router)
```

- [ ] **Step 6: Run tests + full suite + lint + types**

Run: `cd backend && uv run pytest tests/test_orders_api.py -v && uv run pytest -q && uv run ruff check . && uv run mypy app`
Expected: orders_api 5 passed;全 suite 全綠;ruff clean;mypy Success。

- [ ] **Step 7: Commit**

```bash
cd backend && git add app/api/errors.py app/api/routes/orders.py app/main.py tests/test_orders_api.py
git commit -m "feat(backend): public POST /api/orders + PriceChangedError handler"
```

---

## Definition of Done (Phase 4a)

- [ ] `cd backend && uv run pytest -q` → 全數通過(既有 68 + 新增:order_models 3、order_amounts 8、schemas_order 6、order_repo 4、order_service 6、orders_api 5 = 32 新 → 100 total)。
- [ ] `cd backend && uv run ruff check .` → clean。
- [ ] `cd backend && uv run mypy app` → Success。
- [ ] `cd backend && uv run alembic upgrade head` → orders + order_items 遷移已套用。
- [ ] `POST /api/orders` 正常:回 201 + 權威金額 + `order_no`(`MM-XXXXXX`)+ 初始狀態,並扣庫存。
- [ ] 價格不符 → 409 `PRICE_CHANGED` + 新金額明細,且**不扣庫存、不建單**。
- [ ] 庫存不足 → 409 `INSUFFICIENT_STOCK`,且**不扣庫存、不建單**。
- [ ] 未知/停用規格 → 404 `NOT_FOUND`;輸入驗證錯 → 422。
- [ ] 全部任務已提交、plan checkboxes 已勾選。

## 下一階段

- **Phase 4b**:後台訂單管理(列表/篩選/分頁、單筆明細、改狀態並驗證合法轉移),沿用本階段 `orders`/`order_items` 模型與狀態機定義。
- 前端整合:`submitOrder` → `fetch('/api/orders')`(送 `items:[{spec_id, qty}]` + `expected_total`)、`data.js` → `GET /api/products`。
