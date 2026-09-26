## 1. 紅燈

- [ ] 1.1 `tests/test_spec_repo.py` 新增 `lock_many` 測試：回傳 dict、SQL 含 `ORDER BY` 與 `FOR UPDATE`、缺少 id 時不在 dict 中
- [ ] 1.2 新增 `tests/test_order_concurrency.py`：兩個反向順序的訂單並行建立皆成功（使用 committed-session fixture，以同步點確保交錯）
- [ ] 1.3 新增「回應品項順序維持輸入順序」與「缺規格不扣庫存」測試
- [ ] 1.4 執行並確認 1.1、1.2 失敗（1.2 應重現 deadlock）

## 2. 綠燈

- [ ] 2.1 實作 `spec_repo.lock_many`
- [ ] 2.2 `order_service.create_order` 與 `admin_order_service._replace_items` 改用 `lock_many`
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 若 `get_for_update` 已無呼叫者則移除（`change_order_status` 回補庫存也改用 `lock_many`）
- [ ] 3.2 並行測試連續執行 20 次穩定
- [ ] 3.3 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `fix(order): 規格列鎖依 id 排序一次取得，避免並行下單死鎖` 提交
