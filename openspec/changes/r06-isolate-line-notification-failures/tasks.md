## 1. 紅燈

- [ ] 1.1 `tests/test_orders_api.py`：monkeypatch Flex 建構拋 `ValueError`，斷言回應 201 且訂單存在
- [ ] 1.2 `tests/test_orders_api.py`：monkeypatch push 延遲（以 flag 記錄呼叫時間），斷言推播在回應產生後才被呼叫
- [ ] 1.3 `tests/test_line_service.py`：超長品項訂單的 `alt_text` 長度 ≤ 1500 且以「…」結尾
- [ ] 1.4 `tests/test_line_service.py`：`send_order_created` 遇到任意 `Exception` 回傳 False 並記錄 log
- [ ] 1.5 執行並確認上述測試失敗

## 2. 綠燈

- [ ] 2.1 新增 `OrderNotification` dataclass 與轉換函式
- [ ] 2.2 `order_service.create_order` 回傳通知資料，不再直接呼叫推播
- [ ] 2.3 `routes/orders.py` 注入 `BackgroundTasks` 並排入 `line_service.send_order_created`
- [ ] 2.4 `line_service` 改用 `OrderNotification`，外層改捕捉 `Exception`；`alt_text` 截斷
- [ ] 2.5 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 調整既有 `test_order_service.py` 對推播的斷言以符合新介面
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 部署後以測試 OA 實際下單，確認推播仍送達
- [ ] 4.2 以 `fix(line): 訂單推播改為背景任務並隔離所有例外，避免重複下單` 提交
