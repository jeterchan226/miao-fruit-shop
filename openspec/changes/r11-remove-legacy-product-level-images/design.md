## Context

`817c408dc28c` migration 把舊的 `spec_id` 關聯轉成 `is_two_pack`，沒有 spec 關聯的舊圖片則留下 `is_two_pack IS NULL`。前台 `_to_public_spec` 只取 `is_two_pack == spec.is_two_pack` 的圖片，所以 NULL 圖片在前台規格上永遠不會出現，只會經由商品層級 `images` 欄位露出（r12 處理）。

## Goals / Non-Goals

**Goals:** 移除未使用的端點與程式碼；確保沒有資料因此「消失」。

**Non-Goals:** 不改群組端點行為；不把 `is_two_pack` 改成 NOT NULL（交給資料確認後的後續 migration）。

## Decisions

- **先盤點正式資料**：`SELECT count(*) FROM product_images WHERE is_two_pack IS NULL`。
  - 為 0：直接移除程式碼。
  - 不為 0：由店家在後台決定歸到哪一群組；本 change 不自動搬移（無法判斷正確群組）。
- 移除後以測試斷言舊路徑回 404/405，防止日後誤加回。
- `is_two_pack` 欄位改 NOT NULL 需要資料清空後才可做，列為後續工作。

## Risks / Trade-offs

- [仍有外部腳本或舊版前端快取呼叫舊端點] → 前端為 SPA 且每次部署更新；後台只有內部使用者，重新整理即可。

## Resolved Questions

- 正式環境預期沒有 `is_two_pack IS NULL` 的圖片（2026-09-26 確認）；若查詢發現仍有，由店家手動在後台歸類後再上線。
