## MODIFIED Requirements

### Requirement: 顧客下單

系統 SHALL 在 `POST /api/orders` 不需登入即受理訂單，成立時回傳 201 與訂單編號、狀態、訂單品項、金額與成立時間；訂單來源記為顧客下單，初始訂單狀態為待付款。

#### Scenario: 下單成功

- **WHEN** 顧客送出合法訂單且 `expected_total` 與系統計算相符
- **THEN** 系統回傳 201，訂單狀態為 `pending_payment`，訂單來源為 `storefront`

#### Scenario: 公開回應不含後台欄位

- **WHEN** 顧客下單成功
- **THEN** 回應不含顧客個資、LINE 身份與轉帳資訊等後台欄位

#### Scenario: 商店頁送出的付款方式

- **WHEN** 顧客在商店頁送出訂單
- **THEN** 請求的付款方式為 `transfer`
