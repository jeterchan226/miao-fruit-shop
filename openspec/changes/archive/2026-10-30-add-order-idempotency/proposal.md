Ticket: #29

## Why

`POST /api/orders` 沒有任何去重機制，顧客在 LIFF 連點、網路逾時後重試或 WebView 重送，都會成立多張訂單、重複扣庫存、推多則 LINE 通知。訂單以人工對帳轉帳，重複訂單會直接造成管理員與顧客的麻煩。

## What Changes

- 顧客下單接受選填的 `Idempotency-Key` header；同一個 key 最多成立一張訂單，重送時回傳原訂單，不再扣庫存也不再發通知。
- 訂單保存 `idempotency_key`，並以唯一約束擋下同時送達的請求。
- 商店頁每次結帳產生 UUID 隨請求送出；內容未變的重試沿用同一個 key，內容改變或訂單成立後換新 key。
- 商店頁在送出中同步鎖住送出動作，同一輪事件內的連點也只送一次。
- 移除 storefront-checkout「下單沒有冪等性保護」需求。
- 未帶 header 的請求維持現行行為，舊版前端不受影響。

## User Stories

1. 身為顧客，我想要連點或網路不穩時重送也只成立一張訂單，以便不會被重複扣庫存或收到多則通知。
2. 身為顧客，我想要送出逾時後能放心再按一次，以便確認訂單已成立並看到訂單編號。
3. 身為管理員，我想要後台不出現重複訂單，以便對帳時不必判斷哪張才是真的。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `storefront-checkout`: 新增下單冪等性與 `Idempotency-Key` 格式需求，新增商店頁防重複送出需求，移除「下單沒有冪等性保護」。
- `line-integration`: 重送回傳原訂單時不發送 LINE 通知。

## Impact

- 資料庫：`orders` 新增可為 NULL 的唯一欄位與 migration。
- 後端：顧客下單 route、訂單 service、訂單 repository、訂單 model。
- API：`POST /api/orders` 多一個選填 header；回應欄位不變。
- 前端：`api.js` 的 `createOrder`、購物車送單流程，以及新增的 key 管理 module。
- 部署：後端須先於前端上線。
- 其他 ticket：#30 的 retry 包在本 change 的建單邏輯外層；#46（PR #78）也新增 migration，本 change 的 `down_revision` 須於實作時取當下的 head。
