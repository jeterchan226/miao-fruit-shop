# 設計：售完顯示「已售完」+ 訂單明細改用 LINE Flex Message

日期：2026-06-22

## 背景與目標

主要功能皆已完成，此次處理兩項修正：

1. **售完狀態文字**：商品規格售完時，原本顯示「預購中」。需改為「已售完」，不再呈現預購語意。
2. **訂單明細通知美化**：下單成立後透過 LINE 推播的訂單明細目前為純文字。需改用 LINE Flex Message 圖文卡片美化，並保留純文字作為 fallback。

---

## 任務一：售完顯示「已售完」

### 決策

採「保留規格、顯示已售完」方案（非自動下架隱藏）：

- 售完的規格仍顯示於商店頁，狀態標示「已售完」、加入購物車按鈕維持 disabled。
- 補貨後 `stock_qty > 0`，`derive_stock_status` 自動回到 `in`/`low`，按鈕自動恢復可購，**不需管理者手動重新上架**。
- 規格的 `is_active`（上架/下架）開關維持由管理者**手動**控制（例如整檔停賣），與「售完」脫鉤。

理由：本店為單一商品多規格（甘露梨），保留完整規格陣容比忽隱忽現更直覺；且補貨自動恢復，避免「補貨後忘記上架」的疏漏；改動最小，不需動後端與 `is_active`。

### 範圍

純前端文字調整，**不動後端、不動 `is_active`、不新增自動下架邏輯**。

`derive_stock_status` 的 `out` 狀態語意不變（`stock_qty <= 0` → `out`），只調整對應的顯示文字。

### 變更點

| 檔案 | 位置 | 變更 |
|------|------|------|
| `frontend/src/api.js` | 第 51 行 `stockText` 對照表 | `out: '預購中'` → `out: '已售完'` |
| `frontend/src/SpecCard.jsx` | 第 5 行 `stockLabel` | 三元式的 `'預購中'` → `'已售完'` |
| `frontend/src/AdminApp.jsx` | 第 485 行 `STOCK_STATUS_LABELS.out` | `'預購中'` → `'已售完'` |
| `frontend/src/AdminApp.jsx` | 第 488 行 下拉選項 label | `'預購中'` → `'已售完'` |

加入購物車按鈕在售完時的文字（`SpecCard.jsx:123`「已售完」）本就正確，無需更動。

### 驗收

- 商店頁某規格 `stock_qty = 0` 時，狀態欄顯示「已售完」、按鈕 disabled。
- 補貨使 `stock_qty > 0` 後，狀態自動回到「現貨供應」/「剩量不多」，按鈕可購。
- 後台規格列表與狀態下拉選單顯示「已售完」而非「預購中」。
- 全專案前端不再出現「預購中」字樣。

---

## 任務二：訂單明細改用 LINE Flex Message

### 範圍

僅改 `backend/app/services/line_service.py`。推播管道、觸發時機（`order_service.create_order` 末端呼叫 `send_order_created`）、發送條件（token + line_user_id + 通知同意）皆不變。

### 設計

**1. 保留 `_order_text(order) -> str`**

現有純文字函式原樣保留，作為 Flex Message 的 `altText`（推播列表預覽，以及不支援 Flex 的環境 fallback）。

**2. 新增 `_order_flex(order) -> dict`**

回傳一個 LINE Flex Message bubble（dict），版面如下：

- **header**（橘底 `#E89B3C`，白字）：店名「妙媽媽果園」+「訂單已成立」。
- **body**（奶油底，垂直排列）：
  - 訂單編號：`order.order_no`
  - 分隔線
  - 「訂單明細」標題
  - 逐項列出 `order.items`：品名 + 規格 + `x{qty}` 一行，`NT$ {line_total:,}` 靠右一行。
  - 分隔線
  - 金額區：商品小計 `subtotal`、運費 `shipping_fee`、訂單合計 `total`（合計加粗、字級放大、棕字）。
  - 分隔線
  - 收件資訊：收件人 `customer_name`、電話 `customer_phone`、地址（`ship_zipcode ship_city ship_district ship_street`）、希望送達 `preferred_date`。
- **footer**（淡色）：「請於 3 日內完成轉帳，款項確認後將安排出貨。」

**品牌色**（取自 `frontend/assets/colors_and_type.css`）：
- header 底：`#E89B3C`（orange-cta）
- 欄位標籤：`#6B7D52`（sage-700）
- 內文/金額：`#6B4E32`（brown-700）
- 合計強調：`#4A3A2A`（brown-800），bold、size `lg`

金額一律以 `f"NT$ {value:,}"` 格式化，與現有純文字一致。卡片內容欄位與 `_order_text` 對齊，不新增資料來源（無銀行帳號等欄位）。

**3. 調整推播 payload**

`_post_push_message` 送出的 `messages` 由：

```python
{"type": "text", "text": text}
```

改為：

```python
{"type": "flex", "altText": <純文字>, "contents": <bubble dict>}
```

具體做法：`send_order_created` 改為組出 `altText = _order_text(order)`、`contents = _order_flex(order)`，傳入 `_post_push_message`（其簽章調整為接收 altText 與 contents，或接收組好的 message dict）。錯誤處理（HTTPError / OSError 的 logging 與回傳 False）邏輯不變。

### 測試（TDD）

- `_order_flex`：給定一張含多筆 items 的 Order，驗證回傳 dict 的結構含 `type == "bubble"`，且文字內容涵蓋 `order_no`、各品項品名/規格/數量/小計、`subtotal`/`shipping_fee`/`total`、收件人/電話/地址/希望送達。
- `_order_text`：維持既有純文字測試（內容與格式不變）。
- `send_order_created`：既有測試改為驗證送出的 message `type` 為 `flex`、`altText` 等於 `_order_text(order)`、`contents` 為 bubble。發送條件與錯誤處理測試維持不變。

### 驗收

- 下單成立後，LINE 收到的是 Flex 卡片，排版含 header/明細/金額/收件資訊/footer。
- 推播列表預覽（altText）為原純文字內容。
- 後端測試全綠。

---

## 不在範圍內（YAGNI）

- 不新增銀行帳號等新欄位至卡片。
- 不調整推播觸發時機、發送條件或管道。
- 不為售完做自動下架（`is_active`）或庫存連動隱藏。
- 不調整 `derive_stock_status` 的推導邏輯。
