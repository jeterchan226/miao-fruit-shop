## 1. 測試基礎設施

- [ ] 1.1 `tests/conftest.py` 新增 `committed_sessionmaker` fixture（真實 commit，測試後 TRUNCATE 清理）
- [ ] 1.2 以一個 smoke test 確認 fixture 可用，且不影響既有測試隔離

## 2. 紅燈

- [ ] 2.1 新增 `tests/test_admin_order_concurrency.py`：「並行取消同一訂單，庫存只回補一次，其中一個回 `InvalidStatusTransition`」
- [ ] 2.2 新增「取消與編輯並行，編輯回 `OrderNotEditableError`」
- [ ] 2.3 新增 repo 單元測試：`get_by_order_no_for_update` 產生的 SQL 含 `FOR UPDATE`
- [ ] 2.4 執行並確認 2.1、2.2 失敗（重現雙重回補）

## 3. 綠燈

- [ ] 3.1 `order_repo.get_by_order_no_for_update()`（`with_for_update()` + `populate_existing()`）
- [ ] 3.2 `admin_order_service` 三個異動函式改用加鎖讀取
- [ ] 3.3 執行 2.x 測試通過

## 4. 重構與驗證

- [ ] 4.1 抽出 `_get_order_for_update_or_404()` 消除三處重複
- [ ] 4.2 連續執行並行測試 20 次（`pytest --count=20` 或迴圈）確認穩定
- [ ] 4.3 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 5. 收尾

- [ ] 5.1 以 `fix(admin-order): 訂單異動加列鎖，避免並行取消重複回補庫存` 提交
