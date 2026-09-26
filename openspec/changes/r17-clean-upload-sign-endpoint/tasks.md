## 1. 紅燈

- [ ] 1.1 `tests/test_admin_images_api.py`：將 `get_session` override 為拋例外的依賴，簽名端點仍回 200（GCS 以 mock 取代）
- [ ] 1.2 `tests/test_gcs_service.py`：`_make_blob_name("photo.jpg")` 以 `products/uploads/` 開頭
- [ ] 1.3 確認測試失敗

## 2. 綠燈

- [ ] 2.1 `admin_images.sign_upload` 移除 `session` 參數
- [ ] 2.2 `image_service.request_sign`、`gcs_service.sign_upload`、`_make_blob_name` 移除 `product_id`，改用 `UPLOAD_PREFIX`
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 調整 `tests/test_image_service.py` 的呼叫簽章
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`
- [ ] 3.3 後台手動上傳一張照片，確認成功顯示且物件位於 `products/uploads/`

## 4. 收尾

- [ ] 4.1 以 `refactor(images): 簽名上傳移除未使用的 session 與寫死的 product_id` 提交
