## Why

審查 #11：商品照片已在 2026-07 改為依包裝群組（`is_two_pack`：兩粒裝／箱裝）管理，但後端仍保留「商品層級」圖片端點（對應 `product_images.is_two_pack IS NULL`）：`GET/POST /api/admin/products/{id}/images` 與 `PATCH /api/admin/products/{id}/images/reorder`。前端 `AdminApp.jsx` 已不呼叫它們，只剩 `api.js` 裡未使用的 export。死碼增加維護面與攻擊面，也讓人誤以為有兩套圖片模型。

## What Changes

- **BREAKING**：移除 `GET /api/admin/products/{id}/images`、`POST /api/admin/products/{id}/images`、`PATCH /api/admin/products/{id}/images/reorder`（改回 404/405）。
- 保留 `DELETE /api/admin/images/{image_id}`（群組圖片仍在使用）。
- 移除 `image_service.list_images` / `register_image` / `reorder_images` 與 `image_repo.list_by_product`。
- 移除前端 `api.js` 的 `listProductImages`、`registerProductImage`、`reorderProductImages`。
- 若資料庫仍有 `is_two_pack IS NULL` 的圖片，先處理後再上線（見 design）。

## Capabilities

### New Capabilities
- `product-images`: 商品照片僅以包裝群組管理。

### Modified Capabilities
（無）

## Impact

- `backend/app/api/routes/admin_images.py`、`backend/app/services/image_service.py`、`backend/app/repositories/image_repo.py`
- `frontend/src/api.js`
- 測試：`tests/test_admin_images_api.py`、`tests/test_image_service.py`、`tests/test_image_repo.py`
- 與 r12（`Product.image` 與商品層級 `images` 欄位）相關
