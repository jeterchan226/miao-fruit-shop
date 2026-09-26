## ADDED Requirements

### Requirement: 狀態篩選值須合法
系統 SHALL 只接受已定義的訂單狀態作為後台訂單列表的 `status` 篩選值，不合法的值 MUST 回應 422。

#### Scenario: 拼錯的狀態
- **WHEN** 呼叫 `GET /api/admin/orders?status=canceled`
- **THEN** 回應 422

#### Scenario: 合法狀態
- **WHEN** 呼叫 `GET /api/admin/orders?status=cancelled`
- **THEN** 回應 200，只包含已取消訂單

#### Scenario: 未指定狀態
- **WHEN** 呼叫 `GET /api/admin/orders`
- **THEN** 回應 200，包含所有狀態的訂單
