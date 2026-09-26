## Why

審查 #25：`_generate_unique_order_no` 先查詢編號是否存在、再於稍後 insert，兩步之間不是原子操作。兩個並行請求可能產生相同編號，後寫入者觸發 `orders.order_no` 的 unique constraint，拋出未處理的 `IntegrityError`，使用者收到 500。機率極低（32^6 ≈ 10 億種組合），但發生時處理方式錯誤，且整筆訂單（含已鎖定的庫存）會失敗。

## What Changes

- 移除「先查再寫」的檢查，改為 insert 時捕捉 `order_no` unique violation，使用 SAVEPOINT 重新產生編號重試（最多 5 次）。
- 重試耗盡時回 503 `ORDER_NO_UNAVAILABLE`，而非 500。
- 減少一次 DB round trip。

## Capabilities

### New Capabilities
- `order-placement`: 訂單編號的唯一性保證方式。

### Modified Capabilities
（無）

## Impact

- `backend/app/services/order_service.py`、`backend/app/repositories/order_repo.py`、`backend/app/core/exceptions.py`
- 測試：`tests/test_order_service.py`
