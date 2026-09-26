## ADDED Requirements

### Requirement: 下單與後台編輯套用相同品項規則
系統 SHALL 對前台下單與後台編輯訂單品項套用相同的規格存在、啟用、2 粒裝雙數、庫存驗證與價格快照規則。

#### Scenario: 後台以下架規格編輯
- **WHEN** 後台編輯訂單品項，指定 `is_active=false` 的規格
- **THEN** 回應 404 `NOT_FOUND`，訂單與庫存不變

#### Scenario: 後台以 2 粒裝奇數編輯
- **WHEN** 後台編輯訂單品項，2 粒裝規格 qty=3
- **THEN** 回應 409 `EVEN_QTY_REQUIRED`

#### Scenario: 快照價格
- **WHEN** 規格價格為 880 時下單或後台編輯
- **THEN** 產生的 `OrderItem.unit_price=880`、`line_total=880*qty`

### Requirement: 回補庫存規則一致
系統 SHALL 以同一規則回補訂單品項的庫存：每個仍存在的規格增加對應數量，已不存在的規格略過。

#### Scenario: 取消訂單回補
- **WHEN** 取消含規格 S qty=2 的訂單
- **THEN** S 的 `stock_qty` 增加 2
