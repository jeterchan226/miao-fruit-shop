## Why

審查 #9：測試 fixture 用 `Base.metadata.create_all` 建表，完全不跑 Alembic。只要 model 改了卻忘了寫 migration（或 migration 與 model 型別不一致），測試仍然全綠，上線跑 `alembic upgrade head` 後的 schema 與程式不符，正式環境 API 直接 500。

## What Changes

- 新增 migration 測試：在乾淨的資料庫執行 `alembic upgrade head`，再用 autogenerate 比對 model，差異 MUST 為空。
- 新增 `downgrade base` → `upgrade head` 往返測試，確保每個 migration 可回退。
- 測試使用獨立資料庫 `miao_migration_test`，不影響既有 `miao_test`。

## Capabilities

### New Capabilities
- `ci-pipeline`: CI 對資料庫 schema 與 migration 一致性的把關。

### Modified Capabilities
（無）

## Impact

- 新增 `backend/tests/test_migrations.py`
- `backend/alembic/env.py` 可能需要支援以參數覆寫 URL
- CI 的 postgres service 需允許建立額外資料庫（`miao` 使用者已是 owner，可以）
