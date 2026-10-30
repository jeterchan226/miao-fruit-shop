## MODIFIED Requirements

### Requirement: 代客下單不提醒

後台 MUST NOT 對代客下單發出提示音、計入未讀或顯示新訂單橫幅，也不推進已讀標記。

#### Scenario: 新代客下單

- **WHEN** 輪詢發現新的代客下單
- **THEN** 不發出提示音、未讀數不變

#### Scenario: 顧客下單與代客下單同時出現

- **WHEN** 輪詢同時發現訂單來源為 `storefront` 與 `admin` 的新訂單
- **THEN** 未讀數與新訂單橫幅只計入訂單來源為 `storefront` 的訂單
