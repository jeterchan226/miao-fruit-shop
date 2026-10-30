## Context

後台訂單列表查詢由一個 repository 函式組出兩個查詢：計算總筆數、取當頁列表。每個篩選條件都以 `if` 判斷後，把同一個條件各 `.where()` 一次到兩個查詢，共六組重複。#51 已把日期參數換成 `created_from` / `created_before` 並合併，本票可在其後進行。

## Goals / Non-Goals

**Goals:**

- 每個篩選條件只寫一次，總筆數與列表必定共用同一組條件。
- 以測試鎖定總筆數與列表的一致性，讓重構與之後新增篩選都有保護。

**Non-Goals:**

- 不改 API 參數、回應格式、排序、分頁與 `status_counts`（狀態計數隨篩選變動屬 #42）。
- 不新增篩選條件、不調整索引或查詢效能。
- 不動 service、route、schema 與前端。

## Decisions

**1. 先收集條件 list，再一次展開到兩個查詢。**
`conditions: list[ColumnElement[bool]]`，各 `if` 只 append，最後 `count_stmt.where(*conditions)`、`list_stmt.where(*conditions)`。無條件時 `where()` 不加條件，等同現狀。
替代方案：先組共用 base select 再 `.subquery()` 計數：會改變 SQL 形狀，對純重構不值得。

**2. 維持在函式內，不抽 helper。**
目前只有一個使用者，抽出沒有好處。#42 若真的需要重用，再由該票抽出。

**3. 保留既有註解的語意。**
ADR 0005 的時間範圍註解、eager-load 避免 N+1 的註解留在原處。

## Testing Decisions

- **主要入口：HTTP API** `GET /api/admin/orders`（最高且既有的 seam），新情境加在 `backend/tests/test_admin_orders_api.py`，比對回應的總筆數與列表內容。
- **不改的安全網：** `backend/tests/test_order_repo.py`（repository 對測試 DB）與 `test_admin_orders_api.py` 既有的篩選、時間邊界、422 測試，全程不修改，須維持通過。
- **Prior art：** `test_list_orders_filter_by_source`、`test_list_orders_created_range_uses_utc_instants`。
- **紅燈方式：** 純重構下新測試在現狀即通過，屬特徵測試。TDD 的失敗步驟改為：暫時讓某條件只套到列表查詢，確認新測試轉紅後還原，再開始重構。
- 測試資料以唯一的 `source`／`status` 組合或訂單編號前綴隔離，避免被其他訂單影響總筆數斷言。

## Risks / Trade-offs

- [重構漏掉某個條件或改變語意] → 既有測試不動，新測試覆蓋多條件與總筆數。
- [`q` 的 `or_` 條件被展開錯誤] → 整個 `or_` 作為單一元素 append，不拆開。

## Open Questions

（無）
