# #43 order_repo.list_filtered 每個篩選條件重複套用到 count/list 兩個 statement

- 狀態：完成
- OpenSpec change：`dedupe-order-list-filters`（archive 後：`openspec/changes/archive/2026-10-30-dedupe-order-list-filters/`）
- Branch：`claude/laughing-hugle-a81be3`
- 最後更新：2026-10-30

## 做了什麼
- 使用者看不到變更：純重構，API 參數、回應格式與篩選結果不變。

## 決定與偏離
- 偏離 `tasks.md` 一處：`關鍵字比對` 情境原無以電話片段查詢的測試，補上 `test_list_orders_filter_by_phone_fragment`，並列為 task 1.3。
- 紅燈步驟範圍大於 task：六個條件逐一從總筆數查詢移除，每次新測試皆轉紅，之後還原。

## 驗收結果
- [x] 訂單列表篩選 — 依訂單來源篩選：`test_list_orders_filter_by_source`
- [x] 訂單列表篩選 — 無效的訂單來源：`test_list_orders_invalid_source_422`
- [x] 訂單列表篩選 — 關鍵字比對：`test_list_orders_filter_by_phone_fragment`
- [x] 訂單列表篩選 — 時間範圍邊界：`test_list_orders_created_range_uses_utc_instants`
- [x] 訂單列表篩選 — 多個條件同時成立：`test_list_orders_multiple_filters_all_apply`
- [x] 訂單列表篩選 — 總筆數與篩選結果一致：`test_list_orders_total_counts_all_matches_across_pages`（六個條件各一組）

## 留待之後
- 關鍵字 `q` 未跳脫 `%`、`_`：查 `%` 會比對全部訂單。既有行為，本票不改。
- `list_filtered` 的 `status` 為 `str`，`source` 為 `OrderSource`，型別不一致。

## 下一步

## Review
