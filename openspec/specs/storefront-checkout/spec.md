# storefront-checkout Specification

## Purpose

描述顧客從購物車到訂單成立的流程：購物車操作、收件資料填寫與前端驗證、轉帳資訊顯示、顧客下單 API 的請求與回應，以及送出失敗與成功時顧客看到的結果。金額規則見 order-pricing，訂單品項規則見 order-items。
## Requirements
### Requirement: 購物車操作

購物車 SHALL 讓顧客調整數量與移除規格；箱裝以 1 為單位、兩粒裝以 2 為單位增減，數量減到 0 即移除該行，購物車為空時不可前往結帳。

#### Scenario: 數量減到 0

- **WHEN** 顧客把購物車某行的數量減到 0
- **THEN** 該行從購物車移除

#### Scenario: 空購物車

- **WHEN** 購物車沒有任何內容
- **THEN** 購物車顯示「購物車是空的」，不提供前往結帳

### Requirement: 分步結帳流程

商店頁 SHALL 依確認商品、收件資料、轉帳資訊、完成的順序進行結帳，顧客可回到上一步修改，收件資料驗證通過才能進入轉帳資訊。

#### Scenario: 收件資料不合法

- **WHEN** 顧客在收件資料步驟按下一步，但資料未通過驗證
- **THEN** 停留在收件資料步驟並在欄位旁顯示錯誤

#### Scenario: 回到上一步

- **WHEN** 顧客在轉帳資訊步驟按上一步
- **THEN** 回到收件資料步驟且已填資料保留

### Requirement: 收件資料驗證

商店頁 SHALL 在進入轉帳資訊前驗證：姓名、電話、縣市、區域、詳細地址必填；電話須為至少 8 碼的數字、連字號或空白；須選擇送達日且不得早於明天；須勾選 LINE 通知同意。

#### Scenario: 電話格式錯誤

- **WHEN** 電話含有數字、連字號、空白以外的字元或不足 8 碼
- **THEN** 顯示電話格式不正確

#### Scenario: 送達日早於明天

- **WHEN** 送達日早於明天
- **THEN** 顯示送達日不得早於明天

#### Scenario: 未勾選 LINE 通知同意

- **WHEN** 顧客取消勾選 LINE 通知同意
- **THEN** 顯示請勾選 LINE 通知同意，無法進入下一步

### Requirement: 收件資料選項

商店頁 SHALL 以縣市、區域選單選擇地址並自動帶入郵遞區號；送達日預設為明天，日期選單可選範圍為明天起到六個月後；送達時段為不指定、上午 9–13、下午 14–18，預設不指定。

#### Scenario: 選擇區域帶入郵遞區號

- **WHEN** 顧客選擇縣市與區域
- **THEN** 顯示對應郵遞區號

#### Scenario: 重新選擇縣市

- **WHEN** 顧客變更縣市
- **THEN** 區域與郵遞區號清空

### Requirement: 轉帳資訊顯示

商店頁 SHALL 在送出訂單前顯示店家銀行、戶名、帳號與下單後 3 日內完成轉帳的提醒，並列出寄送資訊與訂單金額供顧客確認。

#### Scenario: 進入轉帳資訊步驟

- **WHEN** 顧客通過收件資料驗證
- **THEN** 畫面顯示轉帳帳戶資料、寄送資訊、商品小計、運費與訂單合計

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

### Requirement: 下單請求格式驗證

系統 MUST 以 422 拒絕格式不合的下單請求：訂單品項為空、數量小於 1、送達時段不是 `any`／`am`／`pm`、付款方式不是 `transfer`、`expected_total` 為負數、或出現未定義的頂層欄位。付款方式省略時 SHALL 視為 `transfer`。

#### Scenario: 訂單品項為空

- **WHEN** 請求的 `items` 為空陣列
- **THEN** 系統回傳 422

#### Scenario: 不支援的付款方式

- **WHEN** 請求的付款方式不是 `transfer`
- **THEN** 系統回傳 422

#### Scenario: 省略付款方式

- **WHEN** 請求未帶付款方式
- **THEN** 訂單以 `transfer` 成立

### Requirement: 後端不檢查顧客欄位內容

系統 SHALL 只要求姓名與電話欄位存在，不檢查其內容，也不檢查送達日範圍；這些內容規則僅由前端執行。

#### Scenario: 空白姓名或電話

- **WHEN** 請求繞過前端，以空字串或純空白作為姓名或電話
- **THEN** 訂單仍成立

#### Scenario: 過去的送達日

- **WHEN** 請求繞過前端，帶過去的日期作為送達日
- **THEN** 訂單仍成立

### Requirement: 訂單編號

系統 SHALL 為每張訂單產生 `MM-` 開頭加 6 碼的訂單編號，字元取自排除 I、O、0、1 的大寫英數；候選編號已存在時重新產生，連續 5 次皆已存在則下單失敗並回傳伺服器錯誤。

#### Scenario: 編號格式

- **WHEN** 訂單成立
- **THEN** 訂單編號符合 `MM-` 加 6 碼且不含 I、O、0、1

#### Scenario: 同時產生相同編號

- **WHEN** 兩筆同時下單的請求取得相同編號，且檢查時都未發現已存在
- **THEN** 寫入較晚的請求失敗並回傳伺服器錯誤

### Requirement: 下單失敗提示

商店頁 SHALL 依錯誤類型提示顧客，並停留在轉帳資訊步驟；不自動清空購物車。

#### Scenario: 價格已更新

- **WHEN** 下單回傳 `PRICE_CHANGED`
- **THEN** 顯示新的訂單合計並請顧客重新確認後再送出

#### Scenario: 規格不存在

- **WHEN** 下單回傳 `NOT_FOUND`
- **THEN** 請顧客重新整理頁面後再加入購物車

#### Scenario: 庫存不足

- **WHEN** 下單回傳 `INSUFFICIENT_STOCK`
- **THEN** 顯示庫存不足訊息

### Requirement: 下單成功結果

商店頁 SHALL 在訂單成立後顯示訂單編號、清空購物車，並重新載入商品以反映最新庫存狀態。

#### Scenario: 訂單成立

- **WHEN** 下單成功
- **THEN** 畫面顯示訂單已成立與訂單編號，購物車清空，商品資料重新載入

### Requirement: 下單冪等性

系統 SHALL 以 `POST /api/orders` 的 `Idempotency-Key` header 辨識同一次送單：同一個 key 最多成立一張訂單，重送時 SHALL 回傳 201 與原訂單內容，不扣庫存、不核對金額、不比對請求內容。未帶此 header 的請求 SHALL 視為一筆新訂單。代客下單不適用此機制。

#### Scenario: 相同 key 重送

- **WHEN** 系統收到兩個帶相同 `Idempotency-Key` 的下單請求
- **THEN** 只成立一張訂單，兩次皆回傳 201 且 `order_no` 相同

#### Scenario: 重送不重複扣庫存

- **WHEN** 相同 key 的訂單已成立後再次收到請求
- **THEN** 規格庫存只扣一次

#### Scenario: 原訂單成立後條件改變

- **WHEN** 相同 key 的訂單已成立，之後規格調價或售完，再次收到請求
- **THEN** 系統回傳原訂單，不回傳 `PRICE_CHANGED` 或 `INSUFFICIENT_STOCK`

#### Scenario: 相同 key 同時送達

- **WHEN** 兩個帶相同 key 的請求同時送達
- **THEN** 只成立一張訂單，庫存只扣一次，兩個請求皆回傳 201 且 `order_no` 相同

#### Scenario: 相同 key 同時搶最後庫存

- **WHEN** 兩個帶相同 key 的請求同時送達，且規格庫存只夠成立一張訂單
- **THEN** 只成立一張訂單，兩個請求皆回傳 201 且 `order_no` 相同

#### Scenario: 失敗的請求不佔用 key

- **WHEN** 帶某 key 的請求因 `PRICE_CHANGED` 被拒，之後以相同 key 送出合法請求
- **THEN** 訂單成立

#### Scenario: 不同 key

- **WHEN** 系統收到兩個內容相同但 key 不同的請求
- **THEN** 成立兩張訂單並各自扣庫存

#### Scenario: 未帶 key

- **WHEN** 系統收到兩個未帶 `Idempotency-Key` 且內容相同的請求
- **THEN** 成立兩張訂單並各自扣庫存

#### Scenario: 公開回應不含 key

- **WHEN** 顧客帶 key 下單成功
- **THEN** 回應不含 `idempotency_key`

### Requirement: Idempotency-Key 格式驗證

系統 MUST 以 422 拒絕長度不在 1 到 128 字元之間的 `Idempotency-Key`。

#### Scenario: 空的 key

- **WHEN** 請求的 `Idempotency-Key` 為空字串
- **THEN** 系統回傳 422，不成立訂單

#### Scenario: 過長的 key

- **WHEN** 請求的 `Idempotency-Key` 超過 128 字元
- **THEN** 系統回傳 422，不成立訂單

### Requirement: 商店頁防重複送出

商店頁 SHALL 在送出訂單後立即鎖住送出動作直到請求結束，並在送出中停用送出按鈕。每個請求 SHALL 帶 `Idempotency-Key`：訂單內容未變的重試沿用同一個 key，訂單內容改變或訂單成立後 SHALL 改用新的 key。

#### Scenario: 送出中再次點擊

- **WHEN** 訂單送出中
- **THEN** 送出按鈕不可點選並顯示送出中

#### Scenario: 連續快速點擊

- **WHEN** 顧客在畫面更新前連按兩次送出訂單
- **THEN** 商店頁只發出一個下單請求

#### Scenario: 失敗後重試沿用 key

- **WHEN** 送出因網路錯誤或逾時失敗，顧客未改內容再次送出
- **THEN** 請求帶與前次相同的 `Idempotency-Key`

#### Scenario: 改內容後換 key

- **WHEN** 送出失敗後顧客修改訂單內容再次送出
- **THEN** 請求帶新的 `Idempotency-Key`

#### Scenario: 訂單成立後再次結帳

- **WHEN** 訂單成立後顧客以相同內容再次結帳
- **THEN** 請求帶新的 `Idempotency-Key`，成立另一張訂單

