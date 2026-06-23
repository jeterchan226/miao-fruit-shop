# LINE Rich Menu 設計（程式碼管理版 v1）

日期：2026-06-23
狀態：設計定案，待實作

## 目標

為妙媽媽果園官方帳號建立聊天室底部的 Rich Menu，提供顧客最常用的三個入口，並**全程以程式碼管理**（建立選單、上傳圖片、回覆互動皆在 codebase 內），避免在 OA Manager 後台與程式碼之間兩邊維護。

## 範圍

- 本版實作三格：**立即訂購（A）、匯款回報（C）、購買須知（F）**。
- C、F 的聊天室回覆由**後端 Webhook** 處理。
- 未來擴充：**訂單查詢（B）** 待後端查詢 API 完成後再加入。

> 設計變更紀錄：初版曾規劃以 LINE OA Manager 手動設定（Rich Menu + 關鍵字自動回覆）。為統一維護，改為以 Messaging API 程式化建立 Rich Menu，並自建 Webhook 處理 C／F 回覆。本文件為改寫後版本。

## 實作方式

**Messaging API 程式化建立 Rich Menu + 自建 Webhook**

- Rich Menu：以管理腳本（`cli.py` 子指令）呼叫 Messaging API 建立選單、上傳圖片、設為預設選單。
- C／F 互動：Rich Menu 動作為 **postback**，後端 Webhook 收到事件後以 **Reply API** 在聊天室回覆。
- 沿用現有慣例：**不引入 `line-bot-sdk`**，以標準庫（`hmac`／`hashlib`／`base64`／`urllib`）實作，外呼以 `asyncio.to_thread` 包裝，與既有 `send_order_created` 一致。

## 版面與圖片規格

- 尺寸：**精簡型 Compact，2500 × 843 px**
- 版型：**一排三欄**，每欄 833 × 843 px（座標見下）
- 聊天室選單列文字（chat bar）：`選單`
- 預設狀態：開啟聊天室時自動展開

```
       x=0          x=833        x=1666       x=2500
       ┌────────────┬────────────┬────────────┐
 y=0   │  立即訂購   │  匯款回報   │  購買須知   │
       │    🍐      │    💰      │    📋      │
 y=843 └────────────┴────────────┴────────────┘
          區域 A         區域 C        區域 F
```

各區 bounds（建立 Rich Menu 時使用）：
- A：`{ x: 0,    y: 0, width: 833, height: 843 }`
- C：`{ x: 833,  y: 0, width: 833, height: 843 }`
- F：`{ x: 1666, y: 0, width: 834, height: 843 }`（補滿剩餘寬度）

圖片設計（需另製 2500×843 PNG，可用 Canva 等工具，非程式碼產出）：
- 沿用訂單卡片品牌色：主橘 `#E89B3C`、文字棕 `#6B4E32`、底色奶油 `#FBF3E0`、輔助綠 `#3E8E41`
- 三欄各一圖示 + 中文標籤；欄間以細分隔線或留白區隔
- 標籤：`立即訂購` ／ `匯款回報` ／ `購買須知`
- 圖片放置於 repo（例如 `backend/assets/richmenu/richmenu-compact.png`），由建立腳本上傳

## Rich Menu 各區動作

| 區 | 動作型別 | 內容 |
| --- | --- | --- |
| A 立即訂購 | **URI** | `https://liff.line.me/{LIFF_ID}`（在 LINE 內開 LIFF 商店頁 `/`；`{LIFF_ID}` 同前端 `VITE_MIAO_LIFF_ID`） |
| C 匯款回報 | **postback** | `data: action=report_payment`、`displayText: 我要回報匯款` |
| F 購買須知 | **postback** | `data: action=purchase_notice`、`displayText: 購買須知` |

採用 postback（而非「送出文字」）的理由：`displayText` 仍讓聊天室顯示友善文字，但傳給後端的是結構化 `data`，以 `data` 路由比比對中文字串更穩定。

## Webhook 設計（C／F 回覆）

### 資料流

```
顧客點 Rich Menu 的 C／F
        │ (postback)
        ▼
   LINE Platform ──POST──▶ 後端 /api/line/webhook
                              │ 1. 驗證 X-Line-Signature（HMAC-SHA256）
                              │ 2. 解析 events，取 postback.data + replyToken
                              │ 3. 依 data 路由到對應回覆文案
                              │ 4. 呼叫 Reply API 回覆聊天室
                              ▼
                         顧客在聊天室看到回覆
```

### 簽章驗證

- 目的：webhook 為公開網址，驗證可確保請求**確實來自 LINE**，防止偽造事件與濫用。
- 原理：LINE 以 channel secret 對 **raw request body** 算 HMAC-SHA256 → base64，置於 `X-Line-Signature`。後端用同一把 secret 重算比對。
- 後端須以 `await request.body()` 取得**原始 bytes**（不可重新序列化 JSON，否則簽章不符）。
- 比對失敗 → 回 `400`，不處理。
- 開發便利：未設定 `LINE_CHANNEL_SECRET` 時略過驗證（記 log），正式上線前務必設定。

### 事件路由與回覆

- 僅處理 `type == "postback"` 的事件，依 `postback.data`：
  - `action=report_payment` → 回覆 C 文案
  - `action=purchase_notice` → 回覆 F 文案
  - 其他／未知 → 忽略不回覆
- 回覆走 **Reply API**（`POST /v2/bot/message/reply`，使用 `replyToken`）——不消耗 push 額度。

### 回覆文案（模組常數，比照現有 `BANK_*`）

C（`action=report_payment`）：
```
感謝您的訂購 🍐
請依下列格式回覆，確認款項後盡快為您安排出貨：

訂單編號：MM-______
帳號末5碼：______
匯款金額：______
```

F（`action=purchase_notice`）：
```
🍐 妙媽媽果園 購買須知

・運費 NT$150，單筆滿 NT$5,000 免運
・付款方式：轉帳匯款，請於下單後 3 日內完成
・匯款後請點選「匯款回報」告知帳號末5碼與金額
・確認款項後安排出貨

有任何問題歡迎直接傳訊息給我們 😊
```
- 運費規則來源：`app/core/constants.py`（`SHIPPING_FEE=150`、`FREE_SHIPPING_THRESHOLD=5000`）。此文案為寫死文字，調價時須手動同步。

### 錯誤處理 / 邊界

- LINE 後台「Verify」會送 **events 為空** 的請求 → 正常回 200。
- 缺 secret／token → 記 log、回 200（避免 LINE 端反覆重試），但不回覆訊息。
- Reply API 失敗 → 記 warning、不噴 500（比照 `send_order_created` 容錯）。
- 一律快速回 200，避免 LINE 重送。

## 新增／修改檔案

| 檔案 | 內容 |
| --- | --- |
| `app/core/config.py` | 新增 `line_channel_secret: str = ""` |
| `app/services/line_service.py` | 擴充：`verify_signature(body, signature)`、`reply_message(reply_token, messages)`、`handle_webhook_events(body_bytes, signature)`；C／F 回覆文案常數 |
| `app/api/routes/line_webhook.py` | 新路由 `POST /api/line/webhook`（讀 raw body + header，呼叫 `handle_webhook_events`，回 200／400） |
| `app/main.py` | `include_router(line_webhook.router)` |
| `app/cli.py` | 新子指令 `setup-richmenu`：建立 Rich Menu（A／C／F bounds + 動作）、上傳圖片、設為預設 |
| `backend/assets/richmenu/richmenu-compact.png` | Rich Menu 圖片（需另製） |
| `.env.example` | 新增 `LINE_CHANNEL_SECRET=` |
| `tests/test_line_webhook.py` | 新測試檔 |

## 測試（pytest）

- `verify_signature`：正確簽章 → True；竄改 body／錯 secret → False。
- 路由：`report_payment` postback → C 文案；`purchase_notice` → F 文案；未知 data → 不回覆。
- 端點：合法簽章回 200；非法簽章回 400；空 events 回 200。
- 以 monkeypatch 攔截 Reply API 外呼（不真打 LINE），斷言送出內容正確。

## 部署 / 一次性設定（非程式碼）

- LINE Developers Console：將 **Webhook URL** 設為 `https://<Cloud Run 網址>/api/line/webhook` 並啟用 webhook。
- Cloud Run 環境變數：設定 `LINE_CHANNEL_SECRET`（建議掛 Secret Manager）。
- 部署後執行一次 `setup-richmenu` 指令建立並套用 Rich Menu。

## 相依與注意事項

- A 區依賴 LIFF 已正確設定且 Endpoint 指向 Vercel production 網址。
- Reply API 與簽章驗證皆需正確的 channel access token／channel secret。
- Rich Menu 圖片為手動製作的設計資產，非程式碼產生。

## 未來考量（非本次範圍）

- **B 訂單查詢**：待後端查詢 API。屆時版面由 1×3 改為大型 2×N 新增一格，動作可沿用 postback 並在 webhook 增加路由；若需「已綁定／未綁定不同選單」再評估每位使用者選單切換。
- C 匯款回報日後可升級為 LIFF 表單頁，送出後寫入後端，取代純文字回報。
