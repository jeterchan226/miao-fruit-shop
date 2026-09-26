## Context

`_get_images(p)` 先回傳 `p.images`（所有群組混合），沒有才 fallback `p.image`。前台的 `App.jsx` 在加入購物車時用 `spec.images?.[0]`，商品層級欄位沒有消費者。

## Goals / Non-Goals

**Goals:** 移除欄位與 fallback；資料庫 schema 同步清理。

**Non-Goals:** 不改規格 `images` 的分組邏輯；不處理 `product_images.is_two_pack IS NULL` 的資料（r11）。

## Decisions

- **欄位與 API 同一個 change 移除**：先移 API、下一版才刪欄位雖然更保守，但此欄位已無讀取者，兩階段的價值低。
- migration 採 expand/contract 中的 contract：`deploy.sh` 先建新版不切流量、跑 migration、再切流量。舊版在 migration 後、切流量前仍在服務，而舊版 ORM 的 `SELECT` 會帶 `products.image` → 會 500。**因此需分兩次部署**：
  1. 程式移除所有對 `Product.image` 的讀寫，model 以 `deferred` + 不再映射（先移除 mapped column），部署。
  2. 下一次部署才帶入 drop column migration。
- downgrade 以 nullable `String` 還原欄位，原資料無法還原（於 migration docstring 註明）。

## Resolved Questions

- 兩階段部署已確認可行（2026-09-26）。

## Risks / Trade-offs

- [部署時舊版查詢已刪除的欄位] → 以上述兩階段部署避免。
- [外部仍依賴 `product.images`] → 僅本專案前端使用此 API，已確認無依賴。
