## 1. 紅燈

- [ ] 1.1 `tests/test_order_repo.py`：`q="_"` 只符合含底線的訂單
- [ ] 1.2 `q="%"` 回傳 0 筆
- [ ] 1.3 `tests/test_admin_order_service.py`：只有空白的 `q` 視為未篩選
- [ ] 1.4 `escape_like` 單元測試（含反斜線）
- [ ] 1.5 確認測試失敗

## 2. 綠燈

- [ ] 2.1 實作 `escape_like` 並套用於四個欄位的 `ilike`
- [ ] 2.2 service 層修剪 `q`
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(admin-order): 訂單搜尋跳脫 LIKE 萬用字元` 提交
