## ADDED Requirements

### Requirement: 訂單金額只含小計與運費
系統 SHALL 以 `total = subtotal + shipping_fee` 計算訂單金額，前台訂單回應與 `PRICE_CHANGED` 回應 MUST NOT 包含 `cod_fee` 欄位。

#### Scenario: 建立訂單的回應
- **WHEN** 成功建立訂單
- **THEN** 回應包含 `subtotal`、`shipping_fee`、`total`，且不包含 `cod_fee`

#### Scenario: 價格變動回應
- **WHEN** `expected_total` 與伺服器計算不符
- **THEN** 409 回應包含 `subtotal`、`shipping_fee`、`total`，且不包含 `cod_fee`

### Requirement: 訂單資料不儲存貨到付款手續費
系統 SHALL NOT 在 `orders` 資料表保存貨到付款手續費欄位。

#### Scenario: Migration 後的 schema
- **WHEN** 執行 `alembic upgrade head`
- **THEN** `orders` 資料表沒有 `cod_fee` 欄位
