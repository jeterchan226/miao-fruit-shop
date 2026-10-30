## MODIFIED Requirements

### Requirement: 訂單列表篩選

系統 SHALL 支援以訂單狀態、訂單來源、成立時間範圍、關鍵字與訂單編號篩選，多個條件同時成立：`created_from` 含邊界、`created_before` 不含邊界；關鍵字對顧客姓名、電話、LINE 顯示名稱與 LINE user ID 做不分大小寫的部分比對；訂單編號為完全比對。訂單來源不是 `storefront`／`admin` 時回傳 422。

#### Scenario: 依訂單來源篩選

- **WHEN** 管理員以 `source=admin` 查詢
- **THEN** 只回傳代客下單的訂單

#### Scenario: 無效的訂單來源

- **WHEN** 訂單來源不是 `storefront` 或 `admin`
- **THEN** 系統回傳 422

#### Scenario: 關鍵字比對

- **WHEN** 管理員以電話片段查詢
- **THEN** 回傳電話包含該片段的訂單

#### Scenario: 時間範圍邊界

- **WHEN** 訂單成立時間等於 `created_from`，或等於 `created_before`
- **THEN** 前者包含在結果內，後者不包含

#### Scenario: 多個條件同時成立

- **WHEN** 管理員同時以訂單狀態與訂單來源查詢
- **THEN** 只回傳兩個條件皆符合的訂單

#### Scenario: 總筆數與篩選結果一致

- **WHEN** 管理員帶任一篩選條件查詢，且符合的訂單多於一頁
- **THEN** 回應的總筆數為符合條件的全部筆數，而非全部訂單數或當頁筆數
