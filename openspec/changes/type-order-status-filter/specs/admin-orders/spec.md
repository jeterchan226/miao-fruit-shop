## ADDED Requirements

### Requirement: 訂單狀態篩選值須為有效狀態

系統 SHALL 只接受 `pending_payment`、`ready`、`shipping`、`cancelled` 作為訂單列表的訂單狀態篩選值，其他值 MUST 回傳 422。OpenAPI 文件 SHALL 把訂單狀態篩選參數宣告為 enum，值為上述四種。

#### Scenario: 依訂單狀態篩選

- **WHEN** 管理員以四種訂單狀態之一查詢
- **THEN** 系統回傳 200，只含該訂單狀態的訂單

#### Scenario: 無效的訂單狀態

- **WHEN** 管理員以不存在的訂單狀態查詢
- **THEN** 系統回傳 422

#### Scenario: 空的訂單狀態

- **WHEN** 管理員以空字串作為訂單狀態查詢
- **THEN** 系統回傳 422

#### Scenario: 未帶訂單狀態

- **WHEN** 管理員未帶訂單狀態查詢
- **THEN** 系統回傳 200，不依訂單狀態篩選

#### Scenario: 訂單狀態篩選參數宣告為 enum

- **WHEN** 讀取 OpenAPI 文件中的訂單列表查詢參數
- **THEN** `status` 為 enum，值為 `pending_payment`、`ready`、`shipping`、`cancelled`

## REMOVED Requirements

### Requirement: 訂單狀態篩選值不驗證

**Reason**: 訂單狀態是有限值，寫錯的值回 200 與空列表會被誤認為沒有訂單；訂單來源與變更訂單狀態都已回 422。

**Migration**: 由「訂單狀態篩選值須為有效狀態」取代。呼叫端改送四種訂單狀態之一，或不帶此參數。
