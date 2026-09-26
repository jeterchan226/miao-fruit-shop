## 1. 紅燈

- [ ] 1.1 `tests/test_order_service.py`：預先建立 `MM-AAAAAA`，注入產生器依序回傳 `MM-AAAAAA`、`MM-BBBBBB`，斷言訂單為 `MM-BBBBBB`
- [ ] 1.2 注入產生器永遠回傳既有編號，斷言拋 `OrderNoUnavailableError` 且庫存不變
- [ ] 1.3 確認 1.1、1.2 失敗（目前行為會跳過衝突檢查或拋 `RuntimeError`）

## 2. 綠燈

- [ ] 2.1 `core/exceptions.py` 新增 `OrderNoUnavailableError`（503）
- [ ] 2.2 `create_order` 改為 savepoint 內 insert + 捕捉 unique violation 重試；移除 `_generate_unique_order_no`
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(order): 訂單編號衝突改以 savepoint 重試並回 503` 提交
