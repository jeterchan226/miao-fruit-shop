## MODIFIED Requirements

### Requirement: 僅在訂單成立時通知

系統 SHALL 只在顧客下單成立時發送 LINE 通知；代客下單、訂單狀態變更、編輯訂單與重送回傳原訂單 MUST NOT 發送通知。

#### Scenario: 訂單狀態變更

- **WHEN** 管理員把訂單改為已出貨
- **THEN** 系統不發送 LINE 通知

#### Scenario: 重送回傳原訂單

- **WHEN** 系統收到相同 `Idempotency-Key` 的重送請求並回傳原訂單
- **THEN** 系統不發送 LINE 通知，該訂單只收到一則通知
