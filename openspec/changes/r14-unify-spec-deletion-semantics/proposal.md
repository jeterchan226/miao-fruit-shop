## Why

審查 #14：`product_service` 同時有 `soft_delete_spec`（設 `is_active=False`，沒有任何呼叫者）與 `delete_spec`（硬刪除，`DELETE /api/admin/specs/{id}` 實際使用）。硬刪除後，歷史訂單的 `order_items.spec_id` 指向不存在的規格：後台編輯或取消該訂單時無法回補庫存（程式會靜默略過），前端購物車 localStorage 中的舊 `spec_id` 也會變成 404。兩套語意並存也讓人不確定哪個才正確。

## What Changes

- `DELETE /api/admin/specs/{id}` 改為軟刪除：設 `is_active=False`（並新增 `deleted_at`，與「暫時下架」區分）。
- 移除硬刪除程式路徑；`spec_repo.delete` 刪除。
- 已刪除的規格不出現在公開與後台規格列表；取消歷史訂單時仍可回補其庫存。
- 回應碼維持 204，前端不需改動。

## Capabilities

### New Capabilities
- `product-catalog`: 規格刪除的語意。

### Modified Capabilities
（無）

## Impact

- `backend/app/models/product_spec.py`（新增 `deleted_at`）、新 migration
- `backend/app/services/product_service.py`、`backend/app/repositories/spec_repo.py`
- 測試：`tests/test_product_service.py`、`tests/test_admin_products_api.py`、`tests/test_admin_order_service.py`
