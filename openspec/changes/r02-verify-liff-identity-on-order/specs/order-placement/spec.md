## ADDED Requirements

### Requirement: LINE 身分須經 ID token 驗證
系統 SHALL 在請求帶有 `customer.line_user_id` 時要求 `customer.line_id_token`，並向 LINE 驗證該 token；驗證成功時，訂單的 `line_user_id` MUST 取自 token 的 `sub`，而非請求中的 `line_user_id`。

#### Scenario: 有效 ID token
- **WHEN** 請求帶 `line_id_token`，LINE verify 回傳 `sub=U123`
- **THEN** 訂單成立，`line_user_id=U123`

#### Scenario: 請求的 line_user_id 與 token 不符
- **WHEN** 請求 `line_user_id=Uattacker`，但 token `sub=U123`
- **THEN** 回應 401 `LINE_IDENTITY_INVALID`，不建立訂單、不扣庫存

#### Scenario: 無效或過期 token
- **WHEN** LINE verify 回傳 400
- **THEN** 回應 401 `LINE_IDENTITY_INVALID`，不建立訂單

#### Scenario: 帶 line_user_id 但缺 token
- **WHEN** 請求帶 `line_user_id` 卻沒有 `line_id_token`
- **THEN** 回應 401 `LINE_IDENTITY_INVALID`

#### Scenario: 未使用 LINE 身分下單
- **WHEN** 請求沒有 `line_user_id` 也沒有 `line_id_token`
- **THEN** 訂單照常成立，`line_user_id` 為 null

### Requirement: 下單端點速率限制
系統 SHALL 對 `POST /api/orders` 以來源 IP 施加速率限制，超過上限時 MUST 回應 429 且不建立訂單。

#### Scenario: 超過速率上限
- **WHEN** 同一 IP 在一分鐘內送出超過 `ORDER_RATE_LIMIT` 次下單請求
- **THEN** 超出的請求回應 429 `RATE_LIMITED`
