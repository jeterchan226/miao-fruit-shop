# 售完顯示「已售完」+ 訂單明細 LINE Flex Message Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將商品規格售完狀態文字由「預購中」改為「已售完」，並把下單 LINE 通知由純文字改為 Flex Message 圖文卡片（保留純文字 altText fallback）。

**Architecture:** 任務一為純前端字串調整（無測試框架，以 grep + build 驗證）。任務二、三在 `backend/app/services/line_service.py` 新增 Flex bubble 建構函式與訊息組裝函式，以 pytest 純函式測試（in-memory 建 Order，不碰 DB / 網路）。

**Tech Stack:** React + Vite（前端，無 JS 測試框架）；FastAPI + SQLAlchemy + pytest / pytest-asyncio（後端）；LINE Messaging API Flex Message。

## Global Constraints

- 回覆與文件使用繁體中文（zh-TW）；程式碼、commit、技術名詞可保留英文。
- 金額格式一律 `f"NT$ {value:,}"`，與現有純文字一致。
- 不新增資料欄位（無銀行帳號等）；卡片內容對齊現有 `_order_text`。
- 不更動 `derive_stock_status` 推導邏輯、不動 `is_active`、不做自動下架。
- 不更動 LINE 推播觸發時機、發送條件（token + line_user_id + 通知同意）與錯誤處理行為。
- 前端無單元測試框架，售完文字調整以 `grep` 確認無「預購中」殘留 + `npm run build` 通過驗證。

---

### Task 1: 前端售完狀態文字改「已售完」

**Files:**
- Modify: `frontend/src/api.js:51`
- Modify: `frontend/src/SpecCard.jsx:5`
- Modify: `frontend/src/AdminApp.jsx:485,488`

**Interfaces:**
- Consumes: 無（純文字字面值調整）
- Produces: 無新介面；僅改顯示文字。`derive_stock_status` 的 `out` 狀態語意不變。

- [ ] **Step 1: 改 `frontend/src/api.js` 第 51 行的 stockText 對照表**

把：

```js
  out: '預購中',
```

改為：

```js
  out: '已售完',
```

- [ ] **Step 2: 改 `frontend/src/SpecCard.jsx` 第 5 行的 stockLabel**

把：

```js
const stockLabel = (s) => s === 'in' ? '現貨供應' : s === 'low' ? '剩量不多' : '預購中';
```

改為：

```js
const stockLabel = (s) => s === 'in' ? '現貨供應' : s === 'low' ? '剩量不多' : '已售完';
```

- [ ] **Step 3: 改 `frontend/src/AdminApp.jsx` 第 485 與 488 行**

把第 485 行：

```js
const STOCK_STATUS_LABELS = { in: '現貨供應', low: '剩量不多', out: '預購中' };
```

改為：

```js
const STOCK_STATUS_LABELS = { in: '現貨供應', low: '剩量不多', out: '已售完' };
```

並把第 488 行下拉選項：

```js
  { value: 'out', label: '預購中' },
```

改為：

```js
  { value: 'out', label: '已售完' },
```

- [ ] **Step 4: 確認全前端不再有「預購中」殘留**

Run: `grep -rn "預購中" frontend/src`
Expected: 無任何輸出（exit code 1）。

- [ ] **Step 5: build 驗證**

Run: `cd frontend && npm run build`
Expected: build 成功、無錯誤。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api.js frontend/src/SpecCard.jsx frontend/src/AdminApp.jsx
git commit -m "fix(storefront): 售完狀態文字改為「已售完」，不再顯示「預購中」"
```

---

### Task 2: 新增 `_order_flex` 建構 LINE Flex 卡片

**Files:**
- Modify: `backend/app/services/line_service.py`（在 `_order_text` 之後新增常數與函式）
- Test: `backend/tests/test_line_service.py`（新建）

**Interfaces:**
- Consumes: `app.models.order.Order`（含 `order_no`、`items`、`subtotal`、`shipping_fee`、`total`、`customer_name`、`customer_phone`、`ship_zipcode`/`ship_city`/`ship_district`/`ship_street`、`preferred_date`）；`app.models.order_item.OrderItem`（`product_name`、`spec_label`、`qty`、`line_total`）。
- Produces:
  - `_order_flex(order: Order) -> dict` — 回傳 LINE Flex bubble dict（`{"type": "bubble", ...}`）。
  - 模組常數 `BRAND_HEADER_BG`、`LABEL_COLOR`、`TEXT_COLOR`、`TOTAL_COLOR`、`DIVIDER_COLOR`。
  - 私有 helper `_kv_row(label, value, *, value_color=TEXT_COLOR, value_bold=False) -> dict`、`_item_rows(order) -> list[dict]`、`_divider() -> dict`。

- [ ] **Step 1: 寫失敗測試**

新建 `backend/tests/test_line_service.py`：

```python
from datetime import date

from app.models.order import Order
from app.models.order_item import OrderItem
from app.services import line_service


def _make_order() -> Order:
    order = Order(
        order_no="MM-ABC123",
        status="pending_payment",
        customer_name="王小明",
        customer_phone="0912345678",
        ship_zipcode="100",
        ship_city="台北市",
        ship_district="中正區",
        ship_street="忠孝東路一段1號",
        preferred_date=date(2026, 7, 1),
        delivery_window="any",
        payment_method="transfer",
        subtotal=2680,
        shipping_fee=0,
        cod_fee=0,
        total=2680,
    )
    order.items = [
        OrderItem(product_id=1, spec_id=1, product_name="甘露梨",
                  spec_label="5 台斤家庭箱", unit_price=1880, qty=1, line_total=1880),
        OrderItem(product_id=1, spec_id=2, product_name="甘露梨",
                  spec_label="禮盒", unit_price=800, qty=1, line_total=800),
    ]
    return order


def _all_text(node) -> list[str]:
    """遞迴蒐集 Flex dict 中所有 text 欄位的字串。"""
    found: list[str] = []
    if isinstance(node, dict):
        if node.get("type") == "text" and "text" in node:
            found.append(node["text"])
        for value in node.values():
            found.extend(_all_text(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_all_text(value))
    return found


def test_order_flex_is_bubble_with_key_info():
    order = _make_order()
    flex = line_service._order_flex(order)

    assert flex["type"] == "bubble"

    joined = "\n".join(_all_text(flex))
    # 訂單編號
    assert "MM-ABC123" in joined
    # 明細逐項（品名 + 規格 + 數量、金額）
    assert "甘露梨 5 台斤家庭箱 x1" in joined
    assert "甘露梨 禮盒 x1" in joined
    assert "NT$ 1,880" in joined
    assert "NT$ 800" in joined
    # 金額
    assert "NT$ 2,680" in joined  # 小計 = 合計
    # 收件資訊
    assert "王小明" in joined
    assert "0912345678" in joined
    assert "100 台北市中正區忠孝東路一段1號" in joined
    assert "2026-07-01" in joined
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && pytest tests/test_line_service.py::test_order_flex_is_bubble_with_key_info -v`
Expected: FAIL，`AttributeError: module 'app.services.line_service' has no attribute '_order_flex'`。

- [ ] **Step 3: 在 `line_service.py` 實作 `_order_flex` 與 helper**

在 `_order_text` 函式定義之後、`_post_push_message` 之前，插入：

```python
BRAND_HEADER_BG = "#E89B3C"  # orange-cta
LABEL_COLOR = "#6B7D52"      # sage-700
TEXT_COLOR = "#6B4E32"       # brown-700
TOTAL_COLOR = "#4A3A2A"      # brown-800
DIVIDER_COLOR = "#E8D29E"    # cream-deep


def _divider() -> dict:
    return {"type": "separator", "color": DIVIDER_COLOR, "margin": "md"}


def _kv_row(
    label: str,
    value: str,
    *,
    value_color: str = TEXT_COLOR,
    value_bold: bool = False,
) -> dict:
    return {
        "type": "box",
        "layout": "baseline",
        "contents": [
            {"type": "text", "text": label, "size": "sm",
             "color": LABEL_COLOR, "flex": 2},
            {"type": "text", "text": value, "size": "sm",
             "color": value_color, "flex": 5, "wrap": True, "align": "end",
             "weight": "bold" if value_bold else "regular"},
        ],
    }


def _item_rows(order: Order) -> list[dict]:
    rows: list[dict] = []
    for item in order.items:
        rows.append(
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "contents": [
                    {"type": "text",
                     "text": f"{item.product_name} {item.spec_label} x{item.qty}",
                     "size": "sm", "color": TEXT_COLOR, "flex": 5, "wrap": True},
                    {"type": "text", "text": f"NT$ {item.line_total:,}",
                     "size": "sm", "color": TEXT_COLOR, "flex": 3, "align": "end"},
                ],
            }
        )
    return rows


def _order_flex(order: Order) -> dict:
    address = (
        f"{order.ship_zipcode} "
        f"{order.ship_city}{order.ship_district}{order.ship_street}"
    )
    return {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": BRAND_HEADER_BG,
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "🍐 妙媽媽果園", "color": "#FFFFFF",
                 "weight": "bold", "size": "lg"},
                {"type": "text", "text": "訂單已成立", "color": "#FFFFFF",
                 "size": "sm"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                _kv_row("訂單編號", order.order_no,
                        value_color=TOTAL_COLOR, value_bold=True),
                _divider(),
                {"type": "text", "text": "訂單明細", "weight": "bold",
                 "color": LABEL_COLOR, "size": "sm", "margin": "md"},
                *_item_rows(order),
                _divider(),
                _kv_row("商品小計", f"NT$ {order.subtotal:,}"),
                _kv_row("運費", f"NT$ {order.shipping_fee:,}"),
                _kv_row("訂單合計", f"NT$ {order.total:,}",
                        value_color=TOTAL_COLOR, value_bold=True),
                _divider(),
                _kv_row("收件人", order.customer_name),
                _kv_row("電話", order.customer_phone),
                _kv_row("地址", address),
                _kv_row("希望送達", str(order.preferred_date)),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "12px",
            "contents": [
                {"type": "text",
                 "text": "請於 3 日內完成轉帳，款項確認後將安排出貨。",
                 "size": "xs", "color": TEXT_COLOR, "wrap": True},
            ],
        },
    }
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd backend && pytest tests/test_line_service.py::test_order_flex_is_bubble_with_key_info -v`
Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/line_service.py backend/tests/test_line_service.py
git commit -m "feat(line): 新增 _order_flex 建構訂單明細 Flex 卡片"
```

---

### Task 3: 推播改送 Flex Message（保留純文字 altText）

**Files:**
- Modify: `backend/app/services/line_service.py`（新增 `_build_message`、改 `_post_push_message` 簽章、改 `send_order_created` 傳入）
- Test: `backend/tests/test_line_service.py`（沿用 Task 2 的 `_make_order`，新增測試）

**Interfaces:**
- Consumes: `_order_text(order) -> str`、`_order_flex(order) -> dict`（Task 2）。
- Produces:
  - `_build_message(order: Order) -> dict` — 回傳 `{"type": "flex", "altText": <純文字>, "contents": <bubble>}`。
  - `_post_push_message(token: str, user_id: str, message: dict) -> None` — 簽章由 `text: str` 改為 `message: dict`，送出 `{"to": user_id, "messages": [message]}`。

- [ ] **Step 1: 寫失敗測試**

在 `backend/tests/test_line_service.py` 末端新增：

```python
def test_build_message_is_flex_with_text_alt():
    order = _make_order()
    message = line_service._build_message(order)

    assert message["type"] == "flex"
    assert message["altText"] == line_service._order_text(order)
    assert message["contents"]["type"] == "bubble"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && pytest tests/test_line_service.py::test_build_message_is_flex_with_text_alt -v`
Expected: FAIL，`AttributeError: module 'app.services.line_service' has no attribute '_build_message'`。

- [ ] **Step 3: 實作 `_build_message` 並改 `_post_push_message` 與 `send_order_created`**

在 `_order_flex` 之後新增：

```python
def _build_message(order: Order) -> dict:
    return {
        "type": "flex",
        "altText": _order_text(order),
        "contents": _order_flex(order),
    }
```

把 `_post_push_message` 由：

```python
def _post_push_message(token: str, user_id: str, text: str) -> None:
    body = json.dumps(
        {
            "to": user_id,
            "messages": [{"type": "text", "text": text}],
        }
    ).encode("utf-8")
```

改為：

```python
def _post_push_message(token: str, user_id: str, message: dict) -> None:
    body = json.dumps(
        {
            "to": user_id,
            "messages": [message],
        }
    ).encode("utf-8")
```

（`_post_push_message` 其餘 request 組裝、`urlopen` 不變。）

把 `send_order_created` 內的呼叫由：

```python
        await asyncio.to_thread(
            _post_push_message,
            settings.line_channel_access_token,
            order.line_user_id,
            _order_text(order),
        )
```

改為：

```python
        await asyncio.to_thread(
            _post_push_message,
            settings.line_channel_access_token,
            order.line_user_id,
            _build_message(order),
        )
```

- [ ] **Step 4: 跑測試確認通過**

Run: `cd backend && pytest tests/test_line_service.py -v`
Expected: 三個測試全部 PASS。

- [ ] **Step 5: 跑後端完整測試確認無回歸**

Run: `cd backend && pytest -q`
Expected: 全綠（無因簽章變更導致的失敗）。

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/line_service.py backend/tests/test_line_service.py
git commit -m "feat(line): 訂單通知改送 Flex Message，純文字作為 altText fallback"
```

---

## Self-Review

**1. Spec coverage:**
- 任務一「售完顯示已售完」→ Task 1（api.js / SpecCard.jsx / AdminApp.jsx 三處 + grep + build 驗收）。✓
- 任務二「Flex Message + 純文字 fallback」：`_order_flex` → Task 2；`_build_message` + payload 改送 flex + altText → Task 3。✓
- 「不動 is_active / 自動下架 / derive_stock_status」→ Global Constraints 明列，計畫無相關任務。✓
- 測試（`_order_flex` 結構、`_order_text` 不變、`_build_message` flex+altText）→ Task 2 Step 1 含明細與金額斷言；`_build_message` altText == `_order_text(order)` 即守住純文字格式 → Task 3 Step 1。✓

**2. Placeholder scan:** 無 TBD/TODO；每個 code step 皆有完整程式碼與確切指令。✓

**3. Type consistency:**
- `_order_flex(order) -> dict`：Task 2 定義、Task 3 `_build_message` 使用 `contents` 鍵一致。✓
- `_post_push_message(token, user_id, message: dict)`：Task 3 改簽章後，`send_order_created` 傳入 `_build_message(order)`（dict），型別一致。✓
- 常數 `BRAND_HEADER_BG` 等於 Task 2 定義並於同檔使用。✓
