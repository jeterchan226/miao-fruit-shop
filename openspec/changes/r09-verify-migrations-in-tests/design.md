## Context

`tests/conftest.py` 的 session 級 `engine` fixture 用 `create_all`/`drop_all`，速度快但繞過 Alembic。專案有 9 個 migration，其中 `817c408dc28c` 含資料轉換。

## Goals / Non-Goals

**Goals:** 在 CI 內攔截 model/migration 漂移。

**Non-Goals:** 不把一般測試改成用 Alembic 建表（會變慢，且兩者並存才能各自偵測問題）。

## Decisions

- **使用 `alembic.autogenerate.compare_metadata`** 於 migration 後的連線上比對 `Base.metadata`，而非呼叫 `alembic revision --autogenerate` 產生檔案再檢查內容。
- **獨立資料庫**：測試開頭以 `CREATE DATABASE miao_migration_test`（若不存在），結束後 `DROP`，避免和 `miao_test` 的 `create_all` 表衝突。
- Alembic 以程式方式呼叫（`alembic.command.upgrade(cfg, "head")`），`env.py` 已是 async，需用 `asyncio.to_thread` 或 `run_sync` 包裝，避免在已執行中的事件迴圈內再開迴圈。
- 比對時忽略 `server_default` 字串格式差異（`compare_server_default=False`），避免誤報。

## Risks / Trade-offs

- [既有 model 與 migration 本來就有差異，第一次執行即失敗] → 這正是要找出的問題；若發現差異，另開 migration 修正後再讓測試通過。
- [測試時間增加] → 9 個 migration 預估數秒內，可接受。
