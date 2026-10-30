## Context

`order_repo.list_filtered` 以 `f"%{q}%"` 組模式，再對顧客姓名、電話、LINE 顯示名稱、LINE user ID 做 `.ilike()`。`q` 未跳脫，`%`、`_` 成為萬用字元；Postgres 的 LIKE 預設以 `\` 為跳脫字元，所以 `\` 也不是一般字元。

此行為在 #43 之前就存在，#43 是純重構未變更。PR #89 尚未合併：它把篩選條件改為收進 `conditions` 清單，並在同一條 requirement 新增兩個 scenario。

## Goals / Non-Goals

**Goals:**

- 關鍵字的 `%`、`_`、`\` 只比對字面字元。
- 總筆數與列表結果都套用同一個修正。

**Non-Goals:**

- 不改比對欄位、不分大小寫的部分比對，與 `q` 的型別及長度檢查。
- 不改前端：`listAdminOrders` 已用 `URLSearchParams` 編碼，`%`、`\` 能原樣送達。
- 不改訂單編號篩選：它是完全比對，沒有模式。
- 不為 ILIKE 加索引或調整效能。

## Decisions

- **在 repository 跳脫**：查詢模式是 repository 的細節，route 與 service 繼續傳原始文字。
- **採 #91 的修法方向**：依序把 `\`、`%`、`_` 前面加上 `\`，四個欄位的 `.ilike()` 都帶 `escape="\\"`。`\` 必須最先處理，否則會把後面補上的跳脫字元再跳脫一次。替代方案是 SQLAlchemy 2.0 的 `icontains(q, autoescape=True)`；不採用是為了照 ticket 指定的方向，並維持明確的 `.ilike()`。
- **跳脫邏輯放成 `order_repo` 內的私有函式**：四個欄位共用同一個 pattern，不需要對外的 API。
- **實作以 #43 之後的查詢組裝為基礎**：`## MODIFIED` 的 requirement 也以 #43 的版本為底，保留其 scenario。先於 #43 歸檔會讓那兩個 scenario 提前進入主規格，所以 ticket 標為被 #43 阻擋。

## Testing Decisions

測試入口是 HTTP API：`GET /api/admin/orders?q=...`，放在 `backend/tests/test_admin_orders_api.py`，走真實 Postgres，因為 `escape` 的語意只有資料庫能驗證。不另寫 repository 或純函式測試，跳脫函式是私有細節。

每個新 scenario 一個測試，各建兩筆訂單（字面含該符號與不含），斷言 `items` 與 `total` 都只有前者。`\` 的測試要讓「不含」的訂單仍有其他字元，並以 `params={"q": ...}` 傳入，由 httpx 編碼。

Prior art：#43 新增的 `test_list_orders_filter_by_phone_fragment`（同檔，同樣的 `_make_order`、`_auth_header` 寫法與斷言）。既有 scenario 由 #43 的測試涵蓋，不重寫。

## Risks / Trade-offs

- [#89 合併前實作會衝突] → ticket 以 `Blocked by: #43` 排序；開工時從含 #43 的 dev 開分支。
- [有人依賴 `%` 當萬用字元] → 後台前端未提供此用法，規格也未承諾，不保留。

