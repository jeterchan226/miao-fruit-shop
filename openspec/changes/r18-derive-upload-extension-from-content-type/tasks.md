## 1. 紅燈

- [ ] 1.1 `tests/test_gcs_service.py`：`filename="evil.html"` + `image/png` 產生 `.png`
- [ ] 1.2 參數化測試四種內容類型的副檔名對照
- [ ] 1.3 `tests/test_admin_images_api.py`：`image/svg+xml` 回 422（確認既有行為）
- [ ] 1.4 確認 1.1 失敗

## 2. 綠燈

- [ ] 2.1 `core/constants.py` 新增 `CONTENT_TYPE_EXTENSIONS`
- [ ] 2.2 `schemas/image.py` 的允許清單改用該對照表
- [ ] 2.3 `gcs_service._make_blob_name` 改以 `content_type` 決定副檔名
- [ ] 2.4 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(images): 上傳物件副檔名改由 content_type 決定` 提交
