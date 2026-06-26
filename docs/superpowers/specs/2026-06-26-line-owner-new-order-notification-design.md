# 設計：新訂單成立時 LINE 推播通知店家群組

日期：2026-06-26

## 背景與目標

下單成立後，後端已透過 LINE push 把訂單明細 Flex 卡片推給**客戶**（`line_service.send_order_created`）。

問題：店家端無法即時得知有人下單。原因是 LINE 官方帳號的「聊天」列表排序與通知，由**使用者主動傳入的訊息（inbound webhook event）**驅動；OA 主動 push 出去的訊息不會把對話頂上列表、也不會通知小編。因此若客戶從未傳訊息給 OA，店家就不會自動感知到這筆訂單，只能手動點聊天室或進訂單後台查看。

目標：訂單成立時，額外 push 一則「新訂單」通知到一個只有店家成員的 **LINE 群組**，讓店家即時收到推播，且不依賴客戶是否加好友 / 是否同意通知。

## 決策

- **通知目的地：店家 LINE 群組**（非老闆個人 userId）。理由：push 到群組每則只計 1 則訊息額度，日後要加員工不必改設定；且群組是長期穩定的收件目標。
- **內容：專用精簡 Flex 卡片**（非複用客戶那張）。客戶卡片含轉帳/銀行資訊，對店家無用；店家需要的是「誰下單、聯絡方式、買什麼、何時送、送到哪」。
- **格式：精簡 Flex 卡片**，視覺與客戶端一致，但欄位精簡、移除付款資訊。
- **不做**：多通道通知抽象層（Telegram/Email）、客戶與店家通知合併為單一參數化函式。皆為 YAGNI / 會讓 guard 條件糾結，暫不納入。

## 範圍

僅後端。前端、資料庫 schema、既有客戶通知流程皆不變。

---

## 變更點

### 1. 設定（`backend/app/core/config.py`）

於 `Settings` 的 LINE 區塊新增：

```python
line_owner_group_id: str = ""
```

未設定（空字串）時，店家通知**靜默略過**，不影響下單與客戶通知。`.env.example` 同步補上此鍵。

### 2. 通知函式（`backend/app/services/line_service.py`）

新增 `async def send_new_order_notification(order: Order) -> bool`。

Guard 條件與客戶通知 `send_order_created` 的關鍵差異：

| 條件 | 客戶通知 `send_order_created` | 店家通知（新增） |
|------|------|------|
| `settings.line_channel_access_token` | 需要 | 需要 |
| 目的地 | `order.line_user_id` | `settings.line_owner_group_id` |
| `order.line_notification_consent` | **需要** | **不檢查**（店家一律要知道） |
| `order.line_user_id` | 需要 | **不需要**（客戶沒加好友也要通知店家） |

行為：

- 任一必要條件不滿足（無 token、無 group_id）→ 回傳 `False`，不送。
- 推播失敗（`ApiException` / `Urllib3HTTPError` / `OSError`）→ best-effort：吞例外、`logger.warning` 記錄 `order_no`、回傳 `False`，**不影響交易**。
- 成功 → 回傳 `True`。

複用既有的 `_push_flex(user_id, message)` helper（其 `to` 參數同樣接受 groupId）。

### 3. 精簡 Flex 內容（`backend/app/services/line_service.py`）

新增 `_owner_flex(order)` 與對應的純文字 `alt_text`（複用 / 改寫 `_order_text` 風格皆可，但移除轉帳段落）。

卡片內容（由上而下）：

- **Header**：`🔔 新訂單` + 訂單編號（`order.order_no`）。
- **客戶**：姓名（`order.customer_name`）・電話（`order.customer_phone`）。
- **品項清單**：複用 `_item_rows(order)` 的呈現（品名／規格／數量／小計）。
- **合計**：`order.total`。
- **配送**：希望送達日（`order.preferred_date`）、送達時段（`_delivery_window_label(order)`）。
- **收件地址**：`order.ship_zipcode / ship_city / ship_district / ship_street`。
- **不含**：付款方式、銀行 / 轉帳資訊、匯款須知。

### 4. 串接點（`backend/app/services/order_service.py`）

於 `create_order` 既有客戶通知後新增一行，兩者獨立、互不影響：

```python
await line_service.send_order_created(order)            # 既有：通知客戶
await line_service.send_new_order_notification(order)   # 新增：通知店家群組
```

### 5. 上線步驟：取得 groupId（`backend/app/services/line_service.py` webhook）

`handle_webhook_events` 目前只處理 `PostbackEvent`。新增對 `JoinEvent` 的處理：當 bot 被邀進群組時，`logger.info` 記下 `event.source.group_id`。

操作流程：

1. 把 OA bot 邀進只有店家成員的群組。
2. 從後端 log 讀出 `group_id`。
3. 設定環境變數 `LINE_OWNER_GROUP_ID`（正式環境經既有部署流程設定）。
4. 完成；JoinEvent 的 log 可保留（無害）。

---

## 測試（`backend/tests/test_line_service.py`）

仿既有測試，mock push client，新增針對 `send_new_order_notification` 的案例：

1. **無 group_id** → 不呼叫 push，回傳 `False`。
2. **有 group_id、客戶 `line_notification_consent=False`** → 仍呼叫 push（推到 group_id），回傳 `True`。驗證店家通知不受客戶 consent 影響。
3. **有 group_id、`line_user_id` 為 None** → 仍呼叫 push，回傳 `True`。
4. **push 拋出 `ApiException`** → 回傳 `False`，不向外拋。
5. （可選）驗證送出的 Flex 內容**不含**銀行 / 轉帳字串。

---

## 不變更項目

- 既有客戶通知 `send_order_created` 的行為與 guard 完全不動。
- 前端、資料庫 schema、訂單建立的金額 / 庫存邏輯不動。
- 不新增多通道通知抽象。
