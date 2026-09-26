## Why

審查 #24：`GET /api/admin/orders?status=` 的 `status` 是任意字串。前端傳錯（例如 `canceled`）時不會報錯，只會回空列表，看起來像「沒有訂單」，難以察覺。

## What Changes

- `status` 查詢參數型別改為 `OrderStatus`（r21 的列舉），不合法值回 422。
- 前端維持傳現有狀態字串，不需修改。

## Capabilities

### New Capabilities
- `admin-order-management`: 後台訂單列表狀態篩選的輸入驗證。

### Modified Capabilities
（無）

## Impact

- `backend/app/api/routes/admin_orders.py`、`backend/app/services/admin_order_service.py`、`backend/app/repositories/order_repo.py`（型別）
- 相依 r21；若 r21 未完成，先以 `Literal[...]` 實作，r21 完成後替換
