## 1. 前置確認

- [ ] 1.1 查詢正式資料庫 `is_two_pack IS NULL` 的圖片數量，結果記錄在 PR 說明；若不為 0，先請店家在後台重新歸類

## 2. 紅燈

- [ ] 2.1 `tests/test_admin_images_api.py` 新增：舊的列表、新增、排序三個端點回 404/405
- [ ] 2.2 保留／補強群組端點與 `DELETE /images/{id}` 的既有測試
- [ ] 2.3 確認 2.1 失敗（端點仍存在）

## 3. 綠燈

- [ ] 3.1 移除 `admin_images.py` 中三個舊 route
- [ ] 3.2 移除 `image_service.list_images`、`register_image`、`reorder_images` 與 `image_repo.list_by_product`
- [ ] 3.3 刪除只測試上述函式的舊測試
- [ ] 3.4 執行 2.x 測試通過

## 4. 前端

- [ ] 4.1 移除 `api.js` 的 `listProductImages`、`registerProductImage`、`reorderProductImages`
- [ ] 4.2 `npm run build`、`npm run test` 通過；後台實際操作群組照片上傳、排序、刪除

## 5. 重構與驗證

- [ ] 5.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 6. 收尾

- [ ] 6.1 以 `refactor(images): 移除已不使用的商品層級照片端點` 提交
