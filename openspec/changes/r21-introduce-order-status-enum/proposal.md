## Why

審查 #21：訂單狀態 `"pending_payment"`、`"ready"`、`"shipping"`、`"cancelled"` 以裸字串散落在 `admin_order_service.VALID_TRANSITIONS`、`NOT_EDITABLE_STATUSES`、`order_repo.summary`、`order_service.initial_status`、`schemas.OrderStatusUpdate` 的 `Literal`。拼錯字不會被型別檢查發現（例如 `"canceled"`），新增狀態時也容易漏改其中一處。

## What Changes

- 新增 `OrderStatus(StrEnum)`，所有使用處改用列舉。
- `OrderStatusUpdate.status` 與（r24）列表篩選改用 `OrderStatus` 型別。
- API 的 JSON 值不變（StrEnum 序列化為相同字串），非 BREAKING。
- 以測試確保狀態轉移表涵蓋所有狀態。

## Capabilities

### New Capabilities
- `admin-order-management`: 訂單狀態的定義與轉移規則。

### Modified Capabilities
（無）

## Impact

- 新增 `backend/app/core/order_status.py`（或放入 `constants.py`）
- `backend/app/services/order_service.py`、`admin_order_service.py`、`backend/app/repositories/order_repo.py`、`backend/app/schemas/order.py`
- 與 r24 相依：r24 使用本 change 的列舉
