# admin-orders Specification

## Purpose

描述管理員在後台管理訂單的能力：列表篩選與統計、訂單詳情、訂單狀態轉移、編輯訂單內容、填寫轉帳資訊與代客下單。訂單品項異動規則見 order-items，金額規則見 order-pricing。
## Requirements
### Requirement: 後台訂單 API 需管理員身分

系統 MUST 對所有後台訂單 API 要求有效的管理員 token，否則回傳 401。

#### Scenario: 未帶 token

- **WHEN** 未帶 token 呼叫後台訂單 API
- **THEN** 系統回傳 401

### Requirement: 訂單列表分頁

系統 SHALL 依成立時間新到舊回傳訂單列表，分頁預設第 1 頁、每頁 20 筆，每頁上限 100 筆；頁碼小於 1 或每頁筆數超出範圍時回傳 422。列表項目 SHALL 含訂單編號、訂單狀態、訂單來源、顧客姓名、電話、訂單合計、成立時間、首個訂單品項的商品名稱與訂單品項數。

#### Scenario: 預設分頁

- **WHEN** 管理員未帶分頁參數查詢訂單列表
- **THEN** 回傳第 1 頁最多 20 筆與符合條件的總筆數

#### Scenario: 每頁筆數超過上限

- **WHEN** 每頁筆數大於 100
- **THEN** 系統回傳 422

#### Scenario: 訂單品項摘要

- **WHEN** 訂單有多個訂單品項
- **THEN** 列表項目含首個訂單品項的商品名稱與訂單品項數

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

### Requirement: 時間篩選須帶時區

系統 MUST 只接受帶時區的 `created_from`、`created_before`，以 UTC 時點比對；不帶時區的 datetime 或純日期回傳 422。

#### Scenario: 帶時區偏移

- **WHEN** 時間參數帶 `+08:00`
- **THEN** 系統依對應的 UTC 時點篩選

#### Scenario: 不帶時區

- **WHEN** 時間參數為不帶時區的 datetime
- **THEN** 系統回傳 422

### Requirement: 訂單狀態篩選值不驗證

系統 SHALL 以請求的訂單狀態字串直接比對，不檢查其是否為有效狀態。

#### Scenario: 無效的訂單狀態

- **WHEN** 管理員以不存在的訂單狀態查詢
- **THEN** 系統回傳 200 與空列表

### Requirement: 狀態計數涵蓋全部訂單

列表回應的 `status_counts` SHALL 為全部訂單依訂單狀態的筆數，不受任何篩選條件影響。

#### Scenario: 帶篩選條件

- **WHEN** 管理員以訂單來源篩選列表
- **THEN** `status_counts` 仍為全部訂單的計數

### Requirement: 訂單統計

系統 SHALL 提供訂單統計：總訂單量包含已取消、總營收排除已取消、待出貨筆數為狀態待出貨的訂單數。

#### Scenario: 含已取消訂單

- **WHEN** 有已取消的訂單存在
- **THEN** 總訂單量計入該訂單，總營收不計入

### Requirement: 訂單詳情

系統 SHALL 依訂單編號回傳完整訂單，含顧客、LINE 身份、收件、付款、轉帳資訊、金額與訂單品項；找不到時回傳 404 `NOT_FOUND`。

#### Scenario: 查詢存在的訂單

- **WHEN** 管理員查詢存在的訂單編號
- **THEN** 回傳完整訂單

#### Scenario: 訂單不存在

- **WHEN** 管理員查詢不存在的訂單編號
- **THEN** 系統回傳 404 `NOT_FOUND`

### Requirement: 訂單狀態轉移

系統 SHALL 只允許待付款轉為待出貨或已取消、待出貨轉為已出貨或已取消；已出貨與已取消為終態。其他轉移 MUST 回傳 409 `INVALID_STATUS_TRANSITION`，請求的狀態不是四種訂單狀態之一時回傳 422，訂單不存在時回傳 404。

#### Scenario: 確認收款

- **WHEN** 管理員把待付款訂單改為待出貨
- **THEN** 訂單狀態變為 `ready`

#### Scenario: 不允許的轉移

- **WHEN** 管理員把已出貨訂單改為已取消
- **THEN** 系統回傳 409 `INVALID_STATUS_TRANSITION`

#### Scenario: 無效的狀態值

- **WHEN** 請求的狀態不是 `pending_payment`、`ready`、`shipping`、`cancelled`
- **THEN** 系統回傳 422

#### Scenario: 後台只顯示可轉移的狀態

- **WHEN** 管理員開啟訂單詳情
- **THEN** 狀態選單只列出目前狀態可轉移的目標；終態訂單不可變更

### Requirement: 編輯訂單

系統 SHALL 允許管理員修改待付款與待出貨訂單的顧客、收件、備註與訂單品項，只更新請求中有帶的欄位；明確送 `null` 清空選填欄位，必填欄位送 `null` 回傳 422。已出貨與已取消的訂單 MUST 回傳 409 `ORDER_NOT_EDITABLE`。

#### Scenario: 只改收件資訊

- **WHEN** 管理員只修改地址，不帶訂單品項
- **THEN** 地址更新，訂單品項、下單價、金額與庫存不變，即使規格已調價或已下架

#### Scenario: 清空選填欄位

- **WHEN** 請求對 Email 或備註送 `null`
- **THEN** 該欄位被清空，未帶的欄位不變

#### Scenario: 必填欄位送 null

- **WHEN** 請求對顧客姓名送 `null`
- **THEN** 系統回傳 422

#### Scenario: 不可編輯的狀態

- **WHEN** 管理員編輯已出貨或已取消的訂單
- **THEN** 系統回傳 409 `ORDER_NOT_EDITABLE`

#### Scenario: 未定義的欄位

- **WHEN** 請求帶未定義的欄位
- **THEN** 系統回傳 422

#### Scenario: 訂單不存在

- **WHEN** 管理員編輯不存在的訂單
- **THEN** 系統回傳 404 `NOT_FOUND`

### Requirement: 修改訂單品項須附總額

修改訂單品項時，請求 MUST 帶完整的訂單品項清單與 `expected_total`；缺 `expected_total` 或清單為空時回傳 422。

#### Scenario: 缺總額

- **WHEN** 請求帶訂單品項但未帶 `expected_total`
- **THEN** 系統回傳 422

#### Scenario: 清空訂單品項

- **WHEN** 請求的訂單品項為空陣列
- **THEN** 系統回傳 422

### Requirement: 後台編輯訂單介面

後台 SHALL 只在訂單可編輯時提供編輯；訂單品項未變動時不送出訂單品項，既有訂單至少保留一個訂單品項。可加訂的規格 SHALL 為上架中、有庫存且不在此訂單中的規格；顧客與收件欄位沿用商店頁規則，送達日維持原值時不受不得早於明天的限制。

#### Scenario: 僅剩一個訂單品項

- **WHEN** 訂單只剩一個訂單品項
- **THEN** 不可移除，並提示全部不要請取消訂單

#### Scenario: 已下架規格的訂單品項

- **WHEN** 編輯中的訂單品項規格已下架
- **THEN** 數量欄位停用並標示已下架，數量不可修改

#### Scenario: 價格已更新

- **WHEN** 儲存時回傳 `PRICE_CHANGED`
- **THEN** 顯示新的訂單總額，新增的訂單品項改用最新價格重新試算，既有訂單品項下單價不變

#### Scenario: 保留過去的送達日

- **WHEN** 訂單的送達日已過，管理員修改其他欄位而不改送達日
- **THEN** 可以儲存

### Requirement: 填寫轉帳資訊

系統 SHALL 允許管理員在任何訂單狀態填寫轉帳資訊（帳號後五碼、匯款人姓名、備註），只更新請求中有帶的欄位，明確送 `null` 清空；MUST NOT 改變訂單狀態與庫存。訂單不存在時回傳 404。

#### Scenario: 已出貨訂單

- **WHEN** 管理員對已出貨訂單填寫轉帳資訊
- **THEN** 更新成功

#### Scenario: 省略欄位

- **WHEN** 請求只帶匯款人姓名
- **THEN** 其他轉帳欄位不變

### Requirement: 代客下單

系統 SHALL 在 `POST /api/admin/orders` 讓管理員建立訂單，回傳 201 與完整訂單：訂單來源為 `admin`，付款方式為轉帳，初始狀態為待付款，訂單品項與金額規則同顧客下單。請求 MUST NOT 帶 LINE 身份欄位，帶入時回傳 422；代客下單 MUST NOT 發送 LINE 通知。

#### Scenario: 建立成功

- **WHEN** 管理員送出合法的代客下單
- **THEN** 系統回傳 201，訂單來源為 `admin`，狀態為 `pending_payment`，庫存扣除

#### Scenario: 帶 LINE 欄位

- **WHEN** 代客下單請求帶 LINE user ID
- **THEN** 系統回傳 422

#### Scenario: 不發 LINE 通知

- **WHEN** 代客下單成立
- **THEN** 系統不發送 LINE 通知

#### Scenario: 未帶訂單品項

- **WHEN** 代客下單請求的訂單品項為空
- **THEN** 系統回傳 422

### Requirement: 代客下單介面

後台 SHALL 提供代客下單表單，送出前套用與商店頁相同的顧客與收件規則，且至少一個訂單品項；建立成功後刷新列表並開啟該訂單詳情。

#### Scenario: 沒有訂單品項

- **WHEN** 管理員未新增訂單品項就送出
- **THEN** 顯示請至少新增一個訂單品項

#### Scenario: 建立成功

- **WHEN** 代客下單成功
- **THEN** 關閉表單、刷新列表並開啟新訂單詳情

### Requirement: 後台列表介面的篩選對應

後台 SHALL 依瀏覽器當前時區把選到的日期轉為 UTC 時間範圍（起日 00:00 含、迄日隔天 00:00 不含）；搜尋字以 `MM-` 開頭（不分大小寫）時以訂單編號查詢，否則以關鍵字查詢；訂單來源選項「顧客下單」對應 `storefront`、「代客下單」對應 `admin`，選「全部」時不帶訂單來源。

#### Scenario: 日期區間

- **WHEN** 管理員選擇起訖日期
- **THEN** 請求帶起日當地 00:00 的 `created_from` 與迄日隔天當地 00:00 的 `created_before`

#### Scenario: 搜尋訂單編號

- **WHEN** 搜尋字以 `MM-` 開頭
- **THEN** 請求以 `order_no` 查詢

#### Scenario: 搜尋其他文字

- **WHEN** 搜尋字不是 `MM-` 開頭
- **THEN** 請求以 `q` 查詢

#### Scenario: 依訂單來源選項篩選

- **WHEN** 管理員選擇訂單來源「代客下單」
- **THEN** 請求以 `source=admin` 查詢

### Requirement: 代客下單標籤

後台 SHALL 在訂單列表與訂單詳情以「代客下單」標籤標示訂單來源為 `admin` 的訂單；顧客下單不標示。

#### Scenario: 代客下單顯示標籤

- **WHEN** 訂單來源為 `admin`
- **THEN** 訂單列表與訂單詳情顯示「代客下單」標籤

#### Scenario: 顧客下單不顯示標籤

- **WHEN** 訂單來源為 `storefront`
- **THEN** 訂單列表與訂單詳情不顯示標籤

