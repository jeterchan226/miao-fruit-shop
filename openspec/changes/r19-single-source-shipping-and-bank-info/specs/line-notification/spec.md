## ADDED Requirements

### Requirement: 購買須知與計費規則同源
系統 SHALL 以運費計算所用的同一組常數（`SHIPPING_BY_LAYER`、`FREE_SHIPPING_THRESHOLD`）產生 LINE 購買須知的運費與免運說明。

#### Scenario: 現行設定
- **WHEN** 使用者點選「購買須知」
- **THEN** 回覆包含「一層 $100／二層 $150／三層 $180」與「NT$3,000 免運」

#### Scenario: 調整運費常數
- **WHEN** `SHIPPING_BY_LAYER[1]` 改為 120
- **THEN** 購買須知回覆顯示「一層 $120」

### Requirement: 店家匯款資訊單一來源
系統 SHALL 從單一 `StoreInfo` 常數讀取銀行名稱、分行、戶名、帳號與付款期限，Flex 訊息與替代文字 MUST 使用相同值。

#### Scenario: 訂單 Flex 訊息
- **WHEN** 產生訂單 Flex 訊息
- **THEN** 訊息中的帳號與 `StoreInfo.account_no` 相同，付款期限文字使用 `StoreInfo.payment_due_days`
