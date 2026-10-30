# line-integration Specification

## Purpose

描述系統與 LINE 的整合：在 LIFF 內取得顧客身份與好友狀態、訂單成立後推送 Flex Message 通知、處理官方帳號 webhook 的 postback 回覆，以及建立 Rich Menu。LINE 異常不得影響訂單成立。

## Requirements

### Requirement: 取得 LINE 身份

商店頁 SHALL 在開啟購物車時初始化 LIFF：未設定 LIFF 時視為不可用，未登入時導向 LINE 登入，已登入時取得顧客的 user ID、顯示名稱、頭像與好友狀態並帶入訂單。好友狀態查詢失敗時 SHALL 視為未確認。

#### Scenario: 未設定 LIFF

- **WHEN** 環境未設定 LIFF ID
- **THEN** 結帳頁顯示尚未設定 LIFF，顧客仍可填寫並送出訂單

#### Scenario: 已綁定

- **WHEN** 顧客已登入 LINE
- **THEN** 結帳頁顯示 LINE 顯示名稱與好友狀態，訂單帶入 LINE 身份

#### Scenario: 初始化失敗

- **WHEN** LIFF 初始化失敗
- **THEN** 結帳頁提示請從 LINE 官方帳號開啟，顧客仍可填寫並送出訂單

### Requirement: 加入官方帳號好友

商店頁 SHALL 在顧客已綁定但不是好友時提供加入好友按鈕，開啟設定的加好友連結；顧客返回頁面時 SHALL 重新查詢好友狀態。

#### Scenario: 不是好友

- **WHEN** 已綁定的顧客不是官方帳號好友
- **THEN** 結帳頁顯示加入好友按鈕

#### Scenario: 從加好友頁返回

- **WHEN** 顧客加好友後回到頁面
- **THEN** 好友狀態更新

### Requirement: 訂單成立通知

系統 SHALL 在顧客下單成立後，於已設定 channel access token、訂單有 LINE user ID 且顧客同意通知時，推送一則 Flex Message 給顧客；任一條件不符則不發送。

#### Scenario: 符合條件

- **WHEN** 顧客下單成立且符合發送條件
- **THEN** 系統推送一則通知

#### Scenario: 未設定 token

- **WHEN** 未設定 channel access token
- **THEN** 系統不發送，訂單照常成立

#### Scenario: 沒有 LINE 身份或未同意

- **WHEN** 訂單沒有 LINE user ID，或顧客未同意通知
- **THEN** 系統不發送

### Requirement: 僅在訂單成立時通知

系統 SHALL 只在顧客下單成立時發送 LINE 通知；代客下單、訂單狀態變更與編輯訂單 MUST NOT 發送通知。

#### Scenario: 訂單狀態變更

- **WHEN** 管理員把訂單改為已出貨
- **THEN** 系統不發送 LINE 通知

### Requirement: 通知內容

訂單通知 SHALL 包含訂單編號、訂單品項與行小計、商品小計、運費、訂單合計、收件人、電話、完整地址、希望送達日、送達時段、店家轉帳帳戶、匯款後回報提醒與 3 日內完成轉帳的提醒；運費為 0 時顯示免運費。通知的替代文字 SHALL 含相同的訂單資訊。

#### Scenario: 免運

- **WHEN** 訂單運費為 0
- **THEN** 通知以綠色粗體顯示免運費

#### Scenario: 收取運費

- **WHEN** 訂單有運費
- **THEN** 通知顯示運費金額

#### Scenario: 送達時段

- **WHEN** 訂單的送達時段為 `am`
- **THEN** 通知顯示上午 9–13

### Requirement: 通知失敗不影響訂單

推送通知失敗時，系統 MUST 仍回傳訂單成立並記錄警告，不重試。

#### Scenario: LINE API 失敗

- **WHEN** 推送時 LINE API 回傳錯誤或連線失敗
- **THEN** 下單回應仍為 201

### Requirement: Webhook 簽章驗證

系統 SHALL 驗證 `POST /api/line/webhook` 的 LINE 簽章，簽章不符時回傳 400；未設定 channel secret 時略過事件處理並回傳 200。

#### Scenario: 簽章有效

- **WHEN** webhook 帶有效簽章
- **THEN** 系統回傳 200

#### Scenario: 簽章無效

- **WHEN** webhook 簽章不符
- **THEN** 系統回傳 400

#### Scenario: 未設定 secret

- **WHEN** 未設定 channel secret
- **THEN** 系統不處理事件並回傳 200

### Requirement: Postback 自動回覆

系統 SHALL 對 `action=report_payment` 回覆匯款回報格式，對 `action=purchase_notice` 回覆購買須知；其他 postback 與其他事件類型不回覆。回覆失敗時 MUST 僅記錄警告，webhook 仍回傳 200。

#### Scenario: 匯款回報

- **WHEN** 收到 `action=report_payment` 的 postback
- **THEN** 系統回覆匯款回報的填寫格式

#### Scenario: 購買須知

- **WHEN** 收到 `action=purchase_notice` 的 postback
- **THEN** 系統回覆運費、免運門檻與付款方式說明

#### Scenario: 未知的 postback

- **WHEN** 收到未定義的 postback
- **THEN** 系統不回覆

#### Scenario: 回覆失敗

- **WHEN** 呼叫 LINE 回覆失敗
- **THEN** webhook 不回傳錯誤

### Requirement: 建立 Rich Menu

系統 SHALL 提供管理指令，以指定圖片建立並設為預設的 Rich Menu，含立即訂購（開啟 LIFF）、匯款回報、購買須知三個區塊；缺 LIFF ID 或 channel access token 時 MUST 中止。

#### Scenario: 建立成功

- **WHEN** 以圖片與 LIFF ID 執行指令
- **THEN** 建立三區塊 Rich Menu 並設為預設

#### Scenario: 缺少設定

- **WHEN** 缺 LIFF ID 或 channel access token
- **THEN** 指令中止
