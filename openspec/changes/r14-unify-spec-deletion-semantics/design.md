## Context

`is_active` 目前被用作「下架」：後台列表顯示所有規格（含下架），公開列表只顯示上架。若刪除只設 `is_active=False`，後台會看到「被刪除」的規格重新出現，因此需要另一個狀態。

## Goals / Non-Goals

**Goals:** 保留歷史訂單參照；刪除與下架語意分開。

**Non-Goals:** 不提供「還原已刪除規格」的 UI；不加 `order_items.spec_id` 外鍵（可做但非本 change 必要）。

## Decisions

- **新增 `deleted_at: timestamptz | None`，而非只用 `is_active`**：理由如上。替代方案「新增 `status` enum（active/inactive/deleted）」語意更清楚，但需改寫更多既有 `is_active` 的判斷，成本較高。
- 刪除時同時設 `is_active=False` 與 `deleted_at=now()`，讓所有只檢查 `is_active` 的既有路徑（下單驗證）自動拒絕。
- 後台列表在 `product.specs` relationship 上加 `primaryjoin` 條件或在 service 層過濾 `deleted_at IS NULL`；選擇 service 層過濾，避免 relationship 設定影響回補庫存等需要看到已刪除規格的路徑。
- 移除 `soft_delete_spec` 舊函式，由新的 `delete_spec` 取代。

## Risks / Trade-offs

- [已刪除規格累積] → 數量極少（單一商品數個規格），不需清理。
- [與 r22 修改同一套規格查詢] → r22 的保留函式以 `is_active` 判斷即可，不受影響。
