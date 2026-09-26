## Context

前端先呼叫簽名端點，瀏覽器直接 PUT 到 GCS，再呼叫群組註冊端點把 `public_url` 寫入 `product_images`。簽名時並不知道也不需要商品 id。

## Goals / Non-Goals

**Goals:** 移除無用依賴與魔術數字。

**Non-Goals:** 不搬移既有 GCS 物件；不改前端呼叫方式。

## Decisions

- **移除 `product_id`，而非改成從前端帶入**：簽名在商品層級沒有意義（系統只有一個商品），多一個參數只增加前端負擔。替代方案「路由改為 `/products/{id}/uploads/sign`」是 BREAKING 且無實益。
- 前綴定義為 `gcs_service.UPLOAD_PREFIX = "products/uploads"`。
- `delete_object` 以 bucket URL 前綴判斷，與物件路徑無關，舊物件刪除不受影響。

## Risks / Trade-offs

- [bucket 中新舊路徑並存] → 僅影響命名，不影響讀取與刪除。
