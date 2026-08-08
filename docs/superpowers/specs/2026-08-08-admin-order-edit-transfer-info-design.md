# 訂單後台手動編輯 + 轉帳資訊填寫 — 設計

日期：2026-08-08

## 背景與問題

客戶下單後常臨時要改品項/數量/收件資訊，目前後台只能改狀態，無法編輯訂單內容。另外付款方式僅轉帳，客戶轉帳後 admin 需人工核對，但系統沒有欄位記錄「轉帳帳號後五碼/匯款人姓名」這類核對資訊。

## 目標

1. Admin 可編輯未出貨訂單的客戶資料、收件資訊、備註、商品明細（含金額/庫存正確重算）。
2. Admin 可獨立填寫/更新訂單的轉帳核對資訊，不受訂單狀態限制、不影響庫存或狀態。

## 非目標

- 不做編輯歷史/稽核紀錄表。
- 不因編輯或填轉帳資訊觸發 LINE 通知或自動狀態轉換。
- 不開放編輯 `order_no`、`status`、`payment_method`、任何 `line_*` 身份欄位。

## 資料模型

`orders` 表新增三個 nullable 欄位（migration，down_revision = 現有 head `817c408dc28c`）：

- `transfer_last5: str | None`
- `transfer_payer_name: str | None`
- `transfer_note: str | None`

`app/models/order.py` 同步加三個 `Mapped[str | None]`。

## API

### `PATCH /api/admin/orders/{order_no}`

前置檢查：`order.status` 必須是 `pending_payment` 或 `ready`，否則拋 `OrderNotEditableError`（409）。

Body `AdminOrderUpdate`（全部 optional，只送要改的欄位；`extra="forbid"`）：

```python
class AdminOrderItemUpdate(BaseModel):
    spec_id: int
    qty: int = Field(ge=1)

class AdminOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    ship_zipcode: str | None = None
    ship_city: str | None = None
    ship_district: str | None = None
    ship_street: str | None = None
    preferred_date: date | None = None
    delivery_window: Literal["any", "am", "pm"] | None = None
    note: str | None = None
    items: list[AdminOrderItemUpdate] | None = None
```

`items` 送出時視為整份覆蓋（非逐筆 diff）：

1. 舊品項逐筆 `spec_repo.get_for_update` 鎖定，庫存加回 qty。
2. 新品項逐筆鎖定，檢查 `is_active`、2 粒裝雙數（沿用 `order_service` 規則）。
3. 檢查新品項庫存足夠（此時已加回舊庫存）。
4. 扣新品項庫存；刪舊 `OrderItem`、插新列（`unit_price` 用當下 `spec.price` 重新快照）。
5. `order_service.compute_amounts` 重算 `subtotal/shipping_fee/total`（`cod_fee` 恆 0）。

其他欄位為 `None` 表示不改；直接 setattr 覆蓋非 None 欄位。`items` 未送則品項與金額不動。

回應：`AdminOrderRead`（新增轉帳三欄位）。

### `PATCH /api/admin/orders/{order_no}/transfer`

無狀態限制。Body `AdminOrderTransferUpdate`（全部 optional，`extra="forbid"`）：

```python
class AdminOrderTransferUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transfer_last5: str | None = None
    transfer_payer_name: str | None = None
    transfer_note: str | None = None
```

純 setattr + commit，不動狀態、不動庫存、不動品項/金額。回應同 `AdminOrderRead`。

## 錯誤處理

- 訂單不存在 → `NotFoundError`（404，沿用既有）。
- 狀態不可編輯（shipping/cancelled）→ 新增 `OrderNotEditableError`（409, code `ORDER_NOT_EDITABLE`）。
- 品項含未啟用/不存在規格 → `NotFoundError`（沿用 `create_order` 訊息風格）。
- 2 粒裝非雙數 → `EvenQtyRequiredError`（409，沿用）。
- 庫存不足 → `InsufficientStockError`（409，沿用）。
- 轉帳資訊 PATCH 不做上述任何業務檢查，僅 Pydantic 型別驗證。

## 前端

- `frontend/src/api.js` 新增 `updateAdminOrder(token, orderNo, payload)`、`updateAdminOrderTransfer(token, orderNo, payload)`，比照 `updateAdminOrderStatus` 的 fetch 包裝。
- `AdminApp.jsx` 的 `OrderModal`：
  - 新增「編輯訂單」按鈕切換編輯模式：原本唯讀的收件資訊/商品明細改為可編輯表單（客戶姓名/電話/email、地址四欄、希望送達日期/時段、備註、品項的規格+數量，可增減列），送出呼叫 `updateAdminOrder`，成功後退出編輯模式並刷新 detail。
  - 新增「轉帳資訊」小表單區塊（帳號後五碼、匯款人姓名、備註三個輸入框 + 獨立送出按鈕），呼叫 `updateAdminOrderTransfer`，成功後就地更新 detail，不影響其他 UI 狀態。
  - 訂單狀態為 shipping/cancelled 時「編輯訂單」按鈕停用（但轉帳資訊表單仍可用）。

## 測試

- `tests/test_admin_order_service.py`：
  - `update_order` 改客戶欄位不動品項/金額。
  - `update_order` 換品項 → 庫存正確加回/扣除、金額重算正確。
  - `update_order` 品項含 2 粒裝非雙數 → 拋 `EvenQtyRequiredError`。
  - `update_order` 品項庫存不足 → 拋 `InsufficientStockError`，且未部分寫入（原品項/庫存不變）。
  - `update_order` 於 shipping/cancelled 狀態 → 拋 `OrderNotEditableError`。
  - `update_order` 訂單不存在 → `NotFoundError`。
  - `update_transfer_info` 任意狀態皆可寫入三欄位，且不動 status/items/金額。
- `tests/test_admin_orders_api.py`：兩個 PATCH endpoint 的 200/404/409/422/401 情境。
- 前端沿用手動瀏覽器驗證（UI 表單行為非純函式，不寫 vitest）。

## 影響檔案

- `backend/alembic/versions/`（新 migration）
- `backend/app/models/order.py`
- `backend/app/schemas/order.py`
- `backend/app/core/exceptions.py`
- `backend/app/services/admin_order_service.py`
- `backend/app/api/routes/admin_orders.py`
- `backend/tests/test_admin_order_service.py`
- `backend/tests/test_admin_orders_api.py`
- `frontend/src/api.js`
- `frontend/src/AdminApp.jsx`
- `frontend/assets/admin.css`（編輯表單/轉帳表單樣式）
