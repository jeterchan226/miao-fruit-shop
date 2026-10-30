## 1. 商品部分更新的 null 處理

- [ ] 1.1 寫失敗測試：商品必填欄位逐欄送 `null` 回 422 且資料不變（含同請求帶合法欄位）
- [ ] 1.2 寫測試：商品選填欄位送 `null` 被清空，其他欄位不變
- [ ] 1.3 新增共用 null 檢查 helper 與商品必填欄位常數，於 `ProductUpdate` 加上 model validator，讓測試通過

## 2. 規格部分更新的 null 處理

- [ ] 2.1 寫失敗測試：規格必填欄位逐欄送 `null` 回 422 且資料不變（含同請求帶合法欄位）
- [ ] 2.2 寫測試：規格備註送 `null` 被清空，其他欄位不變
- [ ] 2.3 新增規格必填欄位常數，於 `SpecUpdate` 加上 model validator，讓測試通過

## 3. 訂單改用共用 helper

- [ ] 3.1 確認 `test_update_order_required_field_null_is_422` 與選填清空測試目前通過
- [ ] 3.2 `AdminOrderUpdate._required_fields_not_null` 改呼叫共用 helper，既有測試維持通過

## 4. 驗證

- [ ] 4.1 `uv run ruff check .`
- [ ] 4.2 `uv run mypy app`
- [ ] 4.3 `uv run pytest -q`
