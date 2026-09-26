## Context

目前每個品項一次 `get_for_update` 查詢（N 次 round trip），順序依輸入。r01 會在前面先合併同規格數量。

## Goals / Non-Goals

**Goals:** 消除規格鎖的 deadlock；順便把 N 次查詢降為 1 次。

**Non-Goals:** 不改變訂單列鎖（r04）；不做重試機制。

## Decisions

- **單一查詢 `ORDER BY id FOR UPDATE`**：Postgres 對同一查詢的列依掃描順序加鎖，搭配 `ORDER BY id` 可保證全域一致順序。替代方案「在 Python 排序後逐一查詢」也可行，但仍是 N 次 round trip。
- `spec_repo.lock_many(session, ids) -> dict[int, ProductSpec]`，service 以輸入順序從 dict 取值，保留顯示順序。
- 找不到的 id 以 `set(ids) - dict.keys()` 判斷，回傳第一個缺少的 id 於錯誤訊息。

## Risks / Trade-offs

- [與 r01、r22 改同一段程式] → 實作順序 r01 → r05 → r22；r22 最終把 `lock_many` 包進共用保留函式。
- [死鎖測試需真實並行] → 沿用 r04 的 committed-session fixture；若 r04 尚未完成，本 change 先實作該 fixture。
