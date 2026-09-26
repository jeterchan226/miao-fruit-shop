## Context

`spec` 已用 `with_for_update` 鎖，但訂單本身沒鎖，所以「狀態檢查 → 回補庫存」不是原子操作。現有測試 fixture 把整個測試包在單一連線的 transaction 中並 rollback，無法模擬兩條連線的競爭。

## Goals / Non-Goals

**Goals:** 對同一訂單的異動序列化；有可重現的並行測試。

**Non-Goals:** 不引入樂觀鎖版本欄位；不處理前台下單路徑（r05）。

## Decisions

- **悲觀鎖 `FOR UPDATE`，而非樂觀鎖 `version` 欄位**：樂觀鎖需要 migration、前端要處理衝突重試；後台併發量極低，悲觀鎖簡單且足夠。
- **鎖的順序固定為「訂單 → 規格（依 id 排序）」**，與 r05 的規格排序一致，避免訂單與下單之間互鎖。
- 查詢加 `populate_existing()`，確保 identity map 中已存在的舊物件被刷新為鎖內最新值。
- **測試**：新增 `committed_engine` fixture，每個並行測試用兩個獨立 `AsyncSession` 各自 commit，並在測試後 `TRUNCATE ... RESTART IDENTITY CASCADE` 清理；用 `asyncio.gather` 搭配 `pg_sleep` 或 `asyncio.Event` 製造重疊。

## Risks / Trade-offs

- [並行測試可能不穩定] → 用顯式同步點（第一個交易拿鎖後才放行第二個），不依賴時序巧合。
- [TRUNCATE 會影響共用 test DB 的其他測試] → 並行測試標記 `@pytest.mark.concurrency` 並放在獨立模組，session 級 fixture 的 schema 不受 TRUNCATE 影響。
