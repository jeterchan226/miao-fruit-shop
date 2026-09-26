## Why

審查 #5：`create_order` 與 `_replace_items` 依請求中 `items` 的順序逐一對規格下 `FOR UPDATE`。兩張訂單以相反順序包含相同規格（A: [1,2]、B: [2,1]）同時送出時會互相等待，Postgres 偵測到 deadlock 後終止其中一個交易，使用者收到 500。

## What Changes

- 取得規格列鎖前，先依 `spec_id` 升冪排序（並與 r01 的合併數量一起處理）。
- 改用單一 `SELECT ... WHERE id IN (...) ORDER BY id FOR UPDATE` 一次鎖定所有規格。
- 不影響回應中 `items` 的顯示順序（仍依使用者輸入順序）。

## Capabilities

### New Capabilities
- `order-placement`: 下單時的規格鎖定順序。

### Modified Capabilities
（無）

## Impact

- `backend/app/repositories/spec_repo.py`（新增 `lock_many`）
- `backend/app/services/order_service.py`、`backend/app/services/admin_order_service.py`
- 需使用 r04 引入的 committed-session 測試 fixture
