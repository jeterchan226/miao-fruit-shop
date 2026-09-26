## Why

審查 #6：`create_order` 在 `commit` 之後才 `await line_service.send_order_created(order)`，而 `send_order_created` 只捕捉 `ApiException`、`Urllib3HTTPError`、`OSError`。建構 Flex 訊息時的其他例外（例如 `FlexContainer.from_dict` 驗證失敗、`alt_text` 超過 LINE 的 1500 字上限）會變成 500，但訂單其實已成立；使用者看到失敗後重送，就產生重複訂單並重複扣庫存。另外 LINE 推播延遲會直接拉長下單 API 的回應時間。

## What Changes

- 訂單通知改由 FastAPI `BackgroundTasks` 在回應送出後執行。
- `send_order_created` 捕捉所有 `Exception` 並記錄 log，永不向外拋出。
- `alt_text` 截斷至 LINE 上限（1500 字元）。
- 下單 API 回應不再受 LINE API 延遲或失敗影響。

## Capabilities

### New Capabilities
- `line-notification`: 訂單推播的失敗隔離與訊息限制。

### Modified Capabilities
（無）

## Impact

- `backend/app/api/routes/orders.py`、`backend/app/services/order_service.py`、`backend/app/services/line_service.py`
- 測試：`tests/test_orders_api.py`、`tests/test_line_service.py`
