## ADDED Requirements

### Requirement: 前後端運費常數一致
後端的 `FREE_SHIPPING_THRESHOLD`、`SHIPPING_BY_LAYER` SHALL 與 `frontend/src/pricing.js` 的 `FREE_SHIPPING`、`SHIPPING_BY_LAYER` 相同，不一致時測試 MUST 失敗。

#### Scenario: 常數一致
- **WHEN** 執行一致性測試
- **THEN** 兩邊免運門檻皆為 3000，各層運費皆為 {1:100, 2:150, 3:180}，測試通過

#### Scenario: 只改前端
- **WHEN** `pricing.js` 的 `FREE_SHIPPING` 改為 3500 而後端未改
- **THEN** 一致性測試失敗並列出差異

### Requirement: 共用運費案例
前後端 SHALL 對 `shared/pricing-cases.json` 中每個案例（`items` → `subtotal`、`shipping_fee`、`total`）算出相同結果。

#### Scenario: 2 粒裝與箱裝混合
- **WHEN** 案例為 2 粒裝 2 盒（880）加 5 台斤 1 箱（1880）
- **THEN** 前後端皆算出小計 3640、運費 0、合計 3640
