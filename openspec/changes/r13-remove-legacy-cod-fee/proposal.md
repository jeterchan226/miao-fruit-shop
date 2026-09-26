## Why

審查 #13：付款方式只剩轉帳，店家確認從未收取貨到付款手續費（2026-09-26）。但 `compute_amounts` 的 `cod_fee` 永遠是 0，卻仍出現在 `Order` model、`orders.cod_fee` 欄位、`OrderRead`、`AdminOrderRead`、`PriceChangedError`，以及後台「貨到付款手續費」一列。遺留欄位讓人誤以為仍支援貨到付款，也讓金額公式多一個無意義的項目。

## What Changes

- **BREAKING**：前台 `OrderRead`、後台 `AdminOrderRead` 與 409 `PRICE_CHANGED` 回應全部移除 `cod_fee`。
- `compute_amounts` 回傳值移除 `cod_fee`；`total = subtotal + shipping_fee`。
- 新增 Alembic migration 刪除 `orders.cod_fee` 欄位（分兩階段部署，見 design）。
- 前端後台移除「貨到付款手續費」一列。

## Capabilities

### New Capabilities
- `order-placement`: 訂單金額組成只含商品小計與運費。
- `admin-order-management`: 後台訂單詳情不含貨到付款欄位。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/order_service.py`、`backend/app/services/admin_order_service.py`、`backend/app/schemas/order.py`、`backend/app/core/exceptions.py`、`backend/app/api/errors.py`、`backend/app/models/order.py`
- 新 migration：`drop_orders_cod_fee`
- 前端：`frontend/src/AdminApp.jsx`（676 行的手續費列；79 行 `cod: '貨到付款'` 標籤視資料確認後移除）
- 與 r15（`PriceChangedResponse`）相關
