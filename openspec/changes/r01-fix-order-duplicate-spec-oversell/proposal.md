## Why

審查 #1：`POST /api/orders` 與後台編輯訂單品項時，庫存檢查是「逐行」比對 `spec.stock_qty < qty`，同一 `spec_id` 在 `items` 出現多次時不會加總，導致超賣（庫存可被扣成負數）。甘露梨是限量商品，超賣會直接造成無貨可出的客訴。

## What Changes

- 下單時先依 `spec_id` 合併數量，再以合併後的總量做雙數驗證、庫存驗證、扣庫存，並產生**單一** `OrderItem`。
- 後台 `PATCH /api/admin/orders/{order_no}` 替換品項時套用相同規則。
- 回傳的 `items` 對同一規格只會有一列（原本可能多列）。

## Capabilities

### New Capabilities
- `order-placement`: 前台建立訂單的庫存、金額、品項規則。
- `admin-order-management`: 後台查詢、編輯、變更訂單狀態的規則。

### Modified Capabilities
（無，`openspec/specs/` 目前尚無既有 spec）

## Impact

- `backend/app/services/order_service.py`（`create_order`）
- `backend/app/services/admin_order_service.py`（`_replace_items`）
- 測試：`backend/tests/test_order_service.py`、`backend/tests/test_admin_order_service.py`
- 與 r05（鎖順序）、r22（抽共用保留邏輯）相關，見 design。
