## ADDED Requirements

### Requirement: 訂單異動須序列化
系統 SHALL 在變更訂單狀態、編輯訂單內容、填寫轉帳資訊時，對該訂單列取得排他鎖，並在鎖內 MUST 以最新狀態重新驗證狀態轉移與可編輯性。

#### Scenario: 並行取消同一訂單
- **WHEN** 兩個請求同時將同一張 `pending_payment` 訂單改為 `cancelled`，品項數量 2
- **THEN** 一個成功、另一個回應 409 `INVALID_STATUS_TRANSITION`，規格庫存只增加 2

#### Scenario: 取消與編輯並行
- **WHEN** 一個請求取消訂單、另一個同時編輯該訂單品項
- **THEN** 後完成者看到最新狀態；若訂單已取消，編輯回應 409 `ORDER_NOT_EDITABLE`，庫存與品項保持一致
