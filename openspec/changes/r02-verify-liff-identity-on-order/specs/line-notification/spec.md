## ADDED Requirements

### Requirement: 推播只送給已驗證的 LINE 使用者
系統 SHALL 只在訂單的 `line_user_id` 來自已驗證 ID token 且 `line_notification_consent=true` 時推送訂單 Flex 訊息。

#### Scenario: 未驗證身分不推播
- **WHEN** 訂單沒有經驗證的 `line_user_id`
- **THEN** 不呼叫 LINE push API
