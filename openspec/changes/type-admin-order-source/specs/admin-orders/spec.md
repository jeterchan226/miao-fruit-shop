## MODIFIED Requirements

### Requirement: 訂單列表分頁

系統 SHALL 依成立時間新到舊回傳訂單列表，分頁預設第 1 頁、每頁 20 筆，每頁上限 100 筆；頁碼小於 1 或每頁筆數超出範圍時回傳 422。列表項目 SHALL 含訂單編號、訂單狀態、訂單來源、顧客姓名、電話、訂單合計、成立時間、首個訂單品項的商品名稱與訂單品項數。列表項目的訂單來源在 OpenAPI 文件中 SHALL 宣告為 enum，值為 `storefront`、`admin`。

#### Scenario: 預設分頁

- **WHEN** 管理員未帶分頁參數查詢訂單列表
- **THEN** 回傳第 1 頁最多 20 筆與符合條件的總筆數

#### Scenario: 每頁筆數超過上限

- **WHEN** 每頁筆數大於 100
- **THEN** 系統回傳 422

#### Scenario: 訂單品項摘要

- **WHEN** 訂單有多個訂單品項
- **THEN** 列表項目含首個訂單品項的商品名稱與訂單品項數

#### Scenario: 列表項目的訂單來源宣告為 enum

- **WHEN** 讀取 OpenAPI 文件中的訂單列表項目
- **THEN** `source` 為 enum，值為 `storefront`、`admin`

### Requirement: 訂單詳情

系統 SHALL 依訂單編號回傳完整訂單，含訂單來源、顧客、LINE 身份、收件、付款、轉帳資訊、金額與訂單品項；找不到時回傳 404 `NOT_FOUND`。完整訂單的訂單來源在 OpenAPI 文件中 SHALL 宣告為 enum，值為 `storefront`、`admin`。

#### Scenario: 查詢存在的訂單

- **WHEN** 管理員查詢存在的訂單編號
- **THEN** 回傳完整訂單

#### Scenario: 訂單不存在

- **WHEN** 管理員查詢不存在的訂單編號
- **THEN** 系統回傳 404 `NOT_FOUND`

#### Scenario: 完整訂單的訂單來源宣告為 enum

- **WHEN** 讀取 OpenAPI 文件中的完整訂單
- **THEN** `source` 為 enum，值為 `storefront`、`admin`
