## Why

審查 #18：`gcs_service._make_blob_name` 直接取使用者提供的 `filename` 副檔名。雖然 `content_type` 已限制為四種圖片格式、簽名也鎖住 Content-Type，但 `filename="x.html"` 或 `"x.svg"` 仍會產生對應副檔名的物件名稱；副檔名與實際內容不符，也可能讓某些 CDN 或下載工具依副檔名誤判類型。

## What Changes

- 物件副檔名改由 `content_type` 決定：`image/jpeg→jpg`、`image/png→png`、`image/webp→webp`、`image/gif→gif`。
- `filename` 只保留為前端相容參數，不再影響物件名稱（schema 不變，非 BREAKING）。

## Capabilities

### New Capabilities
- `product-images`: 上傳物件副檔名的決定規則。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/gcs_service.py`、`backend/app/schemas/image.py`（將允許類型與副檔名對照集中）
- 測試：`tests/test_gcs_service.py`
