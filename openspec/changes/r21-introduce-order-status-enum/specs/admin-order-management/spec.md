## ADDED Requirements

### Requirement: 訂單狀態集合固定
系統 SHALL 只使用 `pending_payment`、`ready`、`shipping`、`cancelled` 四種訂單狀態，且狀態轉移表 MUST 為每一種狀態定義允許的下一狀態。

#### Scenario: 轉移表完整
- **WHEN** 檢查狀態轉移表
- **THEN** 表的鍵集合等於全部狀態集合

#### Scenario: 合法轉移
- **WHEN** 將 `pending_payment` 訂單改為 `ready`
- **THEN** 回應 200，狀態為 `ready`

#### Scenario: 非法轉移
- **WHEN** 將 `shipping` 訂單改為 `ready`
- **THEN** 回應 409 `INVALID_STATUS_TRANSITION`

#### Scenario: 未知狀態值
- **WHEN** 呼叫 `PATCH /api/admin/orders/{order_no}/status` 帶 `{"status":"canceled"}`
- **THEN** 回應 422
