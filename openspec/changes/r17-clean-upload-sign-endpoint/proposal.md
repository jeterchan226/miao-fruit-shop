## Why

審查 #17：`POST /api/admin/uploads/sign` 宣告了 `session: SessionDep` 卻從未使用，每次請求都白白取得一個 DB 連線；同時以寫死的 `product_id=0` 呼叫 `request_sign`，所有照片都上傳到 `products/0/`，這個魔術數字看起來像 bug，也和「單一商品」的實際資料（id 通常是 1）不符。

## What Changes

- 移除簽名端點中未使用的 session 依賴。
- `image_service.request_sign` 與 `gcs_service.sign_upload` 移除 `product_id` 參數，物件統一放在具名常數前綴 `products/uploads/`。
- 既有 `products/0/...` 的公開 URL 仍有效（只影響新上傳）。

## Capabilities

### New Capabilities
- `product-images`: 上傳簽名端點的行為。

### Modified Capabilities
（無）

## Impact

- `backend/app/api/routes/admin_images.py`、`backend/app/services/image_service.py`、`backend/app/services/gcs_service.py`
- 測試：`tests/test_admin_images_api.py`、`tests/test_gcs_service.py`、`tests/test_image_service.py`
- 與 r18（副檔名）修改同一函式，建議一起實作
