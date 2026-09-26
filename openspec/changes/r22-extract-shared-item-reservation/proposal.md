## Why

審查 #22：`order_service.create_order` 與 `admin_order_service._replace_items` 各自實作「鎖規格 → 驗證存在／啟用 → 2 粒裝雙數 → 驗庫存 → 扣庫存 → 以現價快照 `OrderItem`」整段流程；`_to_order_read` 與 `_to_admin_order_read` 的品項組裝也重複。r01、r05 的修正必須在兩處各改一次，未來任何規則調整都有漏改一邊的風險。

## What Changes

- 新增 `order_service.reserve_items(session, items) -> ReservedItems`，封裝合併數量（r01）、依 id 排序鎖定（r05）、所有驗證、扣庫存與 `OrderItem` 快照，並回傳金額計算所需資料。
- 新增 `order_service.release_items(session, order_items)`，封裝取消／編輯時的庫存回補。
- `create_order`、`_replace_items`、`change_order_status` 改用上述函式。
- 新增 `_to_item_read()` 共用轉換。
- 純重構，對外行為不變。

## Capabilities

### New Capabilities
- `order-placement`: 前台下單與後台編輯共用同一套品項保留規則。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/order_service.py`、`backend/app/services/admin_order_service.py`
- 相依：建議在 r01、r05 完成後實作
