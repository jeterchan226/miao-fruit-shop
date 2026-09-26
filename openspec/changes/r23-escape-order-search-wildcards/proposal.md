## Why

審查 #23：後台訂單搜尋把 `q` 直接組成 `f"%{q}%"` 做 `ILIKE`，`%` 與 `_` 會被當成萬用字元。例如搜尋 `_` 會符合所有訂單，搜尋含底線的 LINE 顯示名稱會得到錯誤結果。

## What Changes

- 搜尋前跳脫 `\`、`%`、`_`，並在 `ILIKE` 指定 `escape='\\'`。
- 前後空白修剪；空字串視為未篩選。

## Capabilities

### New Capabilities
- `admin-order-management`: 後台訂單關鍵字搜尋的比對語意。

### Modified Capabilities
（無）

## Impact

- `backend/app/repositories/order_repo.py`
- 測試：`tests/test_order_repo.py`
