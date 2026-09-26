## Why

審查 #2：`POST /api/orders` 直接信任前端傳來的 `customer.line_user_id` 與 `line_notification_consent`。任何人都能偽造他人的 LINE userId 並設 consent=true，讓官方帳號對該使用者推送內容可控（收件人姓名、備註等）的 Flex 訊息；同時公開端點沒有速率限制，可被大量假單鎖光限量庫存。

## What Changes

- **BREAKING**：`OrderCreate.customer` 新增 `line_id_token`。只要帶 `line_user_id`，就 MUST 同時帶 `line_id_token`，後端以 LINE `oauth2/v2.1/verify` 驗證，並以 token 的 `sub` 作為唯一可信的 `line_user_id`。
- 驗證失敗回 401 `LINE_IDENTITY_INVALID`；未帶 LINE 身分的訂單照常成立，但不推播。
- `POST /api/orders` 加上以 IP 為鍵的速率限制（預設每分鐘 5 次），超過回 429。
- 新設定：`LINE_LOGIN_CHANNEL_ID`（LIFF 所屬 LINE Login channel，正式環境為 `2007936913`）、`ORDER_RATE_LIMIT`。
- 前端 `Cart.jsx` 送單時附上 `liff.getIDToken()`。

## Capabilities

### New Capabilities
- `order-placement`: 下單身分驗證與速率限制。
- `line-notification`: 訂單推播只送給已驗證身分的使用者。

### Modified Capabilities
（無）

## Impact

- `backend/app/schemas/order.py`、`backend/app/services/order_service.py`、新增 `backend/app/services/line_auth_service.py`、`backend/app/core/config.py`、`backend/app/core/exceptions.py`、`backend/app/main.py`
- 新相依：`httpx`（移至正式相依）、`slowapi`
- 前端：`frontend/src/line.js`、`frontend/src/Cart.jsx`
- Terraform：Cloud Run 新增 `LINE_LOGIN_CHANNEL_ID` 環境變數；CI 需對應 GitHub Secret
- 前後端須同時部署（先後端相容、再前端，見 design）
