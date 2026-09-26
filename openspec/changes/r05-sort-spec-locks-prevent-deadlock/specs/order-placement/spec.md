## ADDED Requirements

### Requirement: 規格鎖以固定順序取得
系統 SHALL 在同一交易中鎖定多個規格時，以 `spec_id` 升冪順序取得列鎖，且訂單品項的呈現順序 MUST 維持使用者輸入的順序。

#### Scenario: 反向順序並行下單不死鎖
- **WHEN** 兩個請求同時下單，一個 `items` 為 [S1, S2]、另一個為 [S2, S1]，庫存皆充足
- **THEN** 兩張訂單皆成功建立，沒有回應 500

#### Scenario: 品項順序保留
- **WHEN** 請求 `items` 為 [S2, S1]
- **THEN** 回應的 `items` 第一列為 S2

#### Scenario: 缺少的規格
- **WHEN** 請求含一個不存在的 `spec_id`
- **THEN** 回應 404 `NOT_FOUND`，且不扣任何庫存
