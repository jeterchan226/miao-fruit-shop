## Why

審查 #4：`change_order_status`、`update_order`、`update_transfer_info` 以一般 `SELECT` 讀取訂單，沒有列鎖。兩個後台分頁（例如平板與電腦）同時取消同一張訂單時，兩邊都通過狀態轉移檢查，庫存被加回兩次；同時編輯品項也會重複回補或扣減。

## What Changes

- `order_repo` 新增 `get_by_order_no_for_update()`（`SELECT ... FOR UPDATE`）。
- 所有會修改訂單的後台流程改用加鎖讀取，並在鎖內重新檢查狀態。
- 新增真實並行測試基礎設施（兩條獨立連線）。

## Capabilities

### New Capabilities
- `admin-order-management`: 後台訂單異動的並行安全。

### Modified Capabilities
（無）

## Impact

- `backend/app/repositories/order_repo.py`、`backend/app/services/admin_order_service.py`
- `backend/tests/conftest.py`（新增 committed-session fixture）、`backend/tests/test_admin_order_concurrency.py`
