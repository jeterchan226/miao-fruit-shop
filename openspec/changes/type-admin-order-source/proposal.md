Ticket: #66

## Why

#49 已把訂單來源集中成單一型別，輸入端（查詢參數、service、repository）都已引用，但後台訂單回應的 `source` 仍宣告為任意字串，OpenAPI 看不出合法值。回應宣告補齊後，API 文件才與訂單來源的實際範圍一致。

## What Changes

- 後台訂單列表項目與完整訂單的 `source` 宣告為訂單來源型別，OpenAPI 顯示 enum（`storefront`、`admin`）。
- JSON 回應內容不變，既有查單與代客下單行為不變。
- 資料欄位仍存字串，不動資料庫結構，不需要 migration。

## User Stories

1. 身為串接後台 API 的開發者，我想要從 OpenAPI 看到訂單來源的合法值，以便不必讀程式碼就能處理每種來源。
2. 身為維護者，我想要訂單來源的輸入與回應使用同一個型別，以便新增來源時只改一處。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `admin-orders`：訂單列表與訂單詳情的訂單來源在 API 契約中限定為 `storefront`、`admin`。

## Impact

- 後台訂單回應 schema 與 OpenAPI 輸出改變；JSON 內容不變，前端不需修改。
- 資料庫不變。但回應改為驗證訂單來源：既有訂單若有其他值，查單 API 會回 500，部署前須確認正式資料。
