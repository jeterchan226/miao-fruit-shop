## MODIFIED Requirements

### Requirement: 顧客下單

系統 SHALL 在 `POST /api/orders` 不需登入即受理訂單，成立時回傳 201 與訂單編號、狀態、訂單品項、金額與成立時間；訂單來源記為顧客下單，初始訂單狀態為待付款。

#### Scenario: 下單成功

- **WHEN** 顧客送出合法訂單且 `expected_total` 與系統計算相符
- **THEN** 系統回傳 201，訂單狀態為 `pending_payment`，訂單來源為 `storefront`

#### Scenario: 公開回應不含後台欄位

- **WHEN** 顧客下單成功，且請求帶有顧客個資、收件資料與 LINE 身份
- **THEN** 回應頂層只有訂單編號、狀態、訂單品項、商品小計、運費、貨到付款手續費、訂單合計與成立時間，每筆訂單品項只有規格識別、商品名稱、規格名稱、單價、數量與小計；不含顧客個資、收件資料、LINE 身份與轉帳資訊等後台欄位
