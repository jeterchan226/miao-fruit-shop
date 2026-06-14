# Phase 4b: Admin Order Management — Design Spec

## 1. 目標

為後台管理員提供訂單管理能力：列表（含篩選、分頁）、單筆明細、改狀態（含狀態機驗證 + 取消自動回補庫存）。

## 2. 範圍

**本階段包含：**
- `GET /api/admin/orders` — 篩選 + 分頁列表
- `GET /api/admin/orders/{order_no}` — 單筆完整明細
- `PATCH /api/admin/orders/{order_no}/status` — 改狀態（狀態機驗證）
- 取消訂單自動回補 `spec.stock_qty`

**不包含：**
- 公開查單端點（`GET /api/orders/{order_no}`）
- 金流 webhook / 付款狀態自動轉移
- 前端整合

## 3. 狀態機

合法轉移規則：

```python
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":          {"confirmed", "cancelled"},
    "pending_payment":  {"confirmed", "cancelled"},
    "confirmed":        {"shipping", "cancelled"},
    "shipping":         {"delivered"},
    "delivered":        set(),   # terminal
    "cancelled":        set(),   # terminal
}
```

- `shipping` 和 `delivered` 不可取消（已寄出）
- 非法轉移 → `409 INVALID_STATUS_TRANSITION`
- 合法轉移到 `cancelled` → 自動回補庫存（見第 7 節）

## 4. API Endpoints

全部掛在 `dependencies=[Depends(get_current_admin)]`（JWT 保護，沿用 Phase 2 / 3 模式）。

### 4.1 GET /api/admin/orders

列表，支援以下 query params（全部選填）：

| 參數 | 型別 | 說明 |
|------|------|------|
| `status` | `str` | 精確比對 `orders.status` |
| `date_from` | `date` | `created_at >= date_from`（含） |
| `date_to` | `date` | `created_at <= date_to` 當日結束（23:59:59.999999） |
| `q` | `str` | ILIKE 模糊搜尋 `customer_name` OR `customer_phone` |
| `order_no` | `str` | 精確比對 `orders.order_no` |
| `page` | `int` | 頁碼，從 1 開始，預設 1 |
| `page_size` | `int` | 每頁筆數，預設 20，最大 100 |

回應：`AdminOrderListResponse`

### 4.2 GET /api/admin/orders/{order_no}

回應：`AdminOrderRead`（完整欄位含 items）

找不到 → 404 `NOT_FOUND`

### 4.3 PATCH /api/admin/orders/{order_no}/status

Body：`OrderStatusUpdate { status: str }`

流程：
1. 查訂單，找不到 → 404
2. 驗轉移合法性，不合法 → 409 `INVALID_STATUS_TRANSITION`
3. 若目標狀態為 `cancelled`，回補庫存
4. 更新 `order.status`，commit
5. 回應：`AdminOrderRead`

## 5. Schemas（加入 app/schemas/order.py）

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
    items: list[OrderItemRead]   # 沿用既有 OrderItemRead
    created_at: datetime
    updated_at: datetime

class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
```

`OrderRead`（Phase 4a 公開用）不改動。

## 6. 三層架構

### 6.1 Repository — order_repo.py（擴充）

新增：

```python
async def list_filtered(
    session: AsyncSession,
    *,
    status: str | None,
    date_from: date | None,
    date_to: date | None,
    q: str | None,
    order_no: str | None,
    page: int,
    page_size: int,
) -> tuple[int, list[Order]]:
    ...
```

- 回傳 `(total_count, items)`
- `date_to` 條件：`created_at < date_to + timedelta(days=1)`（UTC 轉換由應用層負責，此階段直接用 date 邊界）
- `q` 條件：`(customer_name ILIKE %q%) OR (customer_phone ILIKE %q%)`
- 排序：`ORDER BY created_at DESC`
- 分頁：`LIMIT page_size OFFSET (page - 1) * page_size`
- total 用獨立 `SELECT COUNT(*)` 搭配相同 WHERE

### 6.2 Service — admin_order_service.py（新建）

```
app/services/admin_order_service.py
```

含：
- `VALID_TRANSITIONS` dict
- `_to_admin_list_item(order) -> AdminOrderListItem`
- `_to_admin_order_read(order) -> AdminOrderRead`
- `async list_orders(session, *, status, date_from, date_to, q, order_no, page, page_size) -> AdminOrderListResponse`
- `async get_order_detail(session, order_no) -> AdminOrderRead`
- `async change_order_status(session, order_no, new_status) -> AdminOrderRead`

`order_service.py`（`create_order`）完全不動。

### 6.3 Route — admin_orders.py（新建）

```
app/api/routes/admin_orders.py
```

3 個 endpoint，掛 `get_current_admin` dependency。

## 7. 取消自動回補庫存

`change_order_status` 內，當 `new_status == "cancelled"`：

```python
for item in order.items:
    if item.spec_id is not None:
        spec = await spec_repo.get_by_id(session, item.spec_id)
        if spec is not None:
            spec.stock_qty += item.qty
        # spec 已被刪除（spec is None）→ 靜默略過
```

與扣庫存邏輯（`order_service.create_order`）對稱。

## 8. 錯誤處理

| 情境 | HTTP | code |
|------|------|------|
| 訂單不存在 | 404 | `NOT_FOUND`（沿用既有 handler） |
| 非法狀態轉移 | 409 | `INVALID_STATUS_TRANSITION` |

沿用 `app/core/exceptions.py`：

```python
class InvalidStatusTransition(AppError):
    code = "INVALID_STATUS_TRANSITION"
    status_code = 409
```

`app/api/errors.py` 的通用 `AppError` handler 會回傳固定格式 `{"detail": exc.detail, "code": exc.code}`。

## 9. 測試策略（TDD）

**test_admin_order_service.py（db_session）：**
- `list_orders` 無篩選 → 回全部，依 created_at DESC
- `list_orders` 依 status 篩選
- `list_orders` 依 date_from / date_to 篩選
- `list_orders` q 搜尋 customer_name / customer_phone
- `list_orders` order_no 精確比對
- 分頁：total 正確、第 2 頁內容正確
- `get_order_detail` → 回完整 AdminOrderRead（含 items）
- `get_order_detail` 找不到 → NotFoundError
- `change_order_status` 合法轉移 → 狀態更新
- `change_order_status` 非法轉移 → InvalidStatusTransition
- `change_order_status` → cancelled：spec.stock_qty 回補正確
- `change_order_status` → cancelled：spec_id 為 None 時靜默略過

**test_admin_orders_api.py（client）：**
- 未帶 token → 401
- GET /api/admin/orders → 200 + AdminOrderListResponse 結構
- GET /api/admin/orders?status=pending → 只回 pending 訂單
- GET /api/admin/orders/{order_no} → 200 完整明細
- GET /api/admin/orders/MM-NOTEXIST → 404
- PATCH status 合法轉移 → 200 + 新狀態
- PATCH status 非法轉移（shipping → cancelled）→ 409 INVALID_STATUS_TRANSITION
- PATCH status 訂單不存在 → 404

## 10. 檔案異動清單

**新增：**
- `app/services/admin_order_service.py`
- `app/api/routes/admin_orders.py`
- `tests/test_admin_order_service.py`
- `tests/test_admin_orders_api.py`

**修改：**
- `app/schemas/order.py` — 加 admin schemas
- `app/repositories/order_repo.py` — 加 `list_filtered`
- `app/core/exceptions.py` — 沿用 `InvalidStatusTransition`
- `app/api/errors.py` — 沿用通用 `AppError` handler
- `app/main.py` — include `admin_orders` router

## 11. 未來擴充（非本階段）

- 公開查單端點（`GET /api/orders/{order_no}`）
- 前端 `submitOrder` → `POST /api/orders` 串接、`data.js` → `GET /api/products`
- 真實金流 webhook + `pending_payment → confirmed` 自動轉移
