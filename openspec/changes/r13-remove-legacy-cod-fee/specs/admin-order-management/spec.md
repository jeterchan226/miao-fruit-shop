## ADDED Requirements

### Requirement: 後台訂單詳情不含貨到付款手續費
後台訂單詳情 API SHALL NOT 回傳 `cod_fee`，後台畫面 MUST NOT 顯示「貨到付款手續費」。

#### Scenario: 查看訂單詳情
- **WHEN** 已登入管理員呼叫 `GET /api/admin/orders/{order_no}`
- **THEN** 回應不包含 `cod_fee`

#### Scenario: 後台畫面
- **WHEN** 管理員在後台開啟任一訂單詳情
- **THEN** 畫面不顯示「貨到付款手續費」
