## Context

`cod_fee` 在 `Amounts`、兩個 service、三個 schema、例外與 handler 中傳遞，值永遠為 0。店家確認從未收取貨到付款手續費，因此沒有需要保留的歷史資料。前端 `Cart.jsx` 的 `formatApiError` 只讀 `data.total`，不讀 `cod_fee`。

## Goals / Non-Goals

**Goals:** 程式、API、資料庫全面移除 `cod_fee`。

**Non-Goals:** 不改變 `payment_method` 欄位本身。

## Decisions

- **連同資料庫欄位一起刪除**：無歷史資料需保留（2026-09-26 確認）。
- **兩階段部署**（與 r12 相同原因）：`deploy.sh` 在 migration 後、切流量前，舊版仍在服務，舊版 ORM 的 `SELECT`/`INSERT` 會帶 `orders.cod_fee`，欄位若已刪除會 500。
  1. 第一階段：程式不再讀寫 `cod_fee`（移除 mapped column），部署。此時 DB 欄位仍在；由於欄位是 `NOT NULL` 且無預設，新程式 insert 會失敗 → 第一階段的 migration 先將欄位改為 `server_default '0'`（expand，舊版不受影響）。
  2. 第二階段：下一次部署帶入 drop column migration。
- downgrade：加回 `cod_fee INTEGER NOT NULL DEFAULT 0`，所有資料為 0（與原值相同，無資料遺失）。
- 前端 `AdminApp.jsx:79` 的 `cod: '貨到付款'` 付款方式標籤：先查 `SELECT count(*) FROM orders WHERE payment_method = 'cod'`，為 0 則一併移除。

## Risks / Trade-offs

- [第一階段漏加 server_default 導致新訂單寫入失敗] → 以測試斷言「model 不含 `cod_fee` 時仍可建立訂單」，並在 r09 migration 測試中涵蓋。

## Resolved Questions

- 沒有任何貨到付款手續費的歷史訂單，欄位可刪除（2026-09-26 確認）。
