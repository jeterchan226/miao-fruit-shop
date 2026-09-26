## Why

審查 #15：`schemas/order.py` 定義了 `PriceChangedResponse`（docstring 寫「供文件/前端參考」），但沒有任何 route 引用它，是死碼。同時 OpenAPI 文件完全沒有描述 `POST /api/orders` 可能回傳的 409 錯誤（`PRICE_CHANGED`、`INSUFFICIENT_STOCK`、`EVEN_QTY_REQUIRED`）與 404，前端只能讀原始碼才知道錯誤形狀。

## What Changes

- 新增共用 `ErrorResponse`（`detail`、`code`）schema。
- `POST /api/orders` 宣告 `responses`：404 / 409 使用 `ErrorResponse`，並以 `PriceChangedResponse` 描述 `PRICE_CHANGED` 的額外欄位。
- 其他使用 `AppError` 的端點至少宣告 `ErrorResponse`（後台端點 401、404、409）。
- 以測試鎖住 OpenAPI 文件內容。

## Capabilities

### New Capabilities
- `api-contract`: API 錯誤回應形狀在 OpenAPI 文件中的宣告。

### Modified Capabilities
（無）

## Impact

- `backend/app/schemas/`（新增 `error.py`）、`backend/app/api/routes/orders.py`、後台 routes
- 新增 `tests/test_openapi.py`
- 與 r13（`PriceChangedResponse` 移除 `cod_fee`）相關：若 r13 先完成，本 change 沿用其欄位
