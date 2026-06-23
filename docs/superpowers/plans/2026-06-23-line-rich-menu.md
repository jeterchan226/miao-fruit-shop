# LINE Rich Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以 line-bot-sdk v3 程式化建立妙媽媽果園官方帳號的 Rich Menu（立即訂購／匯款回報／購買須知），並自建 webhook 用 Reply API 回覆 C／F，同時將既有推播遷移到 SDK。

**Architecture:** Rich Menu 由 `cli.py` 子指令透過 SDK 建立、上傳圖片、設為預設選單。C／F 為 postback 動作，後端 `/api/line/webhook` 以 `WebhookParser` 驗簽 + 解析事件，依 `postback.data` 路由到對應文案，用 `MessagingApi.reply_message` 回覆。既有 `send_order_created` 由手寫 urllib 改為 `MessagingApi.push_message` + `FlexMessage`（沿用既有 flex dict）。

**Tech Stack:** Python 3.13、FastAPI、line-bot-sdk v3、pytest／pytest-asyncio、uv。

## Global Constraints

- Python 版本：>= 3.13。
- 套件管理：用 `uv`（`uv add` / `uv run`），不手改 lock。
- Lint：ruff，select `E,F,I,UP,B`，line-length 100。每個 task 完成前 `uv run ruff check .` 須通過。
- 型別：mypy strict（`uv run mypy app`）須通過。
- LINE SDK：使用 `line-bot-sdk` v3（`linebot.v3` 命名空間）；既有推播一併遷移，不保留手寫 urllib。
- 外呼網路（reply／push）以 `asyncio.to_thread` 包裝，與既有非同步流程一致。
- 文案為繁體中文，須與下方程式碼逐字一致（含 emoji、全形標點、換行）。
- Rich Menu 尺寸固定 2500×843；三區 bounds：A `(0,0,833,843)`、C `(833,0,833,843)`、F `(1666,0,834,843)`。
- postback data：C=`action=report_payment`、F=`action=purchase_notice`。
- 既有測試（`tests/test_line_service.py` 的 `_order_flex`／`_order_text` 相關）行為不得改變。

---

### Task 1: 導入 line-bot-sdk 與設定欄位

**Files:**
- Modify: `backend/pyproject.toml`（新增相依，經 `uv add`）
- Modify: `backend/app/core/config.py:38`（在 `line_channel_access_token` 後新增欄位）
- Modify: `backend/.env.example`（新增兩個變數）
- Test: `backend/tests/test_line_config.py`（新檔）

**Interfaces:**
- Produces: `settings.line_channel_secret: str`（預設 `""`）、`settings.line_liff_id: str`（預設 `""`）；`line-bot-sdk` 可被 import。

- [ ] **Step 1: 寫失敗測試**

建立 `backend/tests/test_line_config.py`：

```python
from app.core.config import settings


def test_linebot_sdk_importable():
    from linebot.v3 import WebhookParser  # noqa: F401


def test_settings_have_line_webhook_fields():
    assert settings.line_channel_secret == ""
    assert settings.line_liff_id == ""
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && uv run pytest tests/test_line_config.py -v`
Expected: FAIL（`ModuleNotFoundError: linebot` 或 `AttributeError: ... line_channel_secret`）

- [ ] **Step 3: 安裝套件**

Run: `cd backend && uv add line-bot-sdk`
Expected: `pyproject.toml` 出現 `line-bot-sdk`，`uv.lock` 更新。

- [ ] **Step 4: 新增設定欄位**

在 `backend/app/core/config.py` 將：

```python
    line_channel_access_token: str = ""
```

改為：

```python
    line_channel_access_token: str = ""
    line_channel_secret: str = ""
    line_liff_id: str = ""
```

- [ ] **Step 5: 更新 .env.example**

在 `backend/.env.example` 的 `LINE_CHANNEL_ACCESS_TOKEN=...` 那行下方新增：

```
# LINE webhook 簽章驗證用（LINE Developers Console → Channel secret）
LINE_CHANNEL_SECRET=<line channel secret>
# Rich Menu「立即訂購」開啟的 LIFF App ID（同前端 VITE_MIAO_LIFF_ID）
LINE_LIFF_ID=1234567890-AbcdEfgh
```

- [ ] **Step 6: 跑測試確認通過**

Run: `cd backend && uv run pytest tests/test_line_config.py -v`
Expected: PASS（2 passed）

- [ ] **Step 7: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/core/config.py backend/.env.example backend/tests/test_line_config.py
git commit -m "chore(line): 導入 line-bot-sdk 與 webhook/liff 設定欄位"
```

---

### Task 2: 既有推播遷移到 SDK

把 `send_order_created` 從手寫 urllib 改為 `MessagingApi.push_message` + `FlexMessage`。`_order_flex`／`_order_text` 保持不變。

**Files:**
- Modify: `backend/app/services/line_service.py`（替換 import、`_build_message`、`_post_push_message`、`send_order_created`）
- Modify: `backend/tests/test_line_service.py`（替換 `test_build_message_is_flex_with_text_alt`，新增推播測試）

**Interfaces:**
- Consumes: `settings.line_channel_access_token`、`_order_flex(order) -> dict`、`_order_text(order) -> str`。
- Produces: `_configuration() -> Configuration`、`_flex_message(order) -> FlexMessage`、`_push_flex(user_id: str, message: FlexMessage) -> None`、`send_order_created(order) -> bool`（行為不變：未設 token／無 user_id／無 consent 回 False）。

- [ ] **Step 1: 改寫測試**

在 `backend/tests/test_line_service.py`，刪除 `test_build_message_is_flex_with_text_alt`，改為：

```python
def test_flex_message_alt_text_matches_order_text():
    order = _make_order()
    msg = line_service._flex_message(order)
    assert msg.alt_text == line_service._order_text(order)


async def test_send_order_created_pushes_flex(monkeypatch):
    order = _make_order()
    order.line_user_id = "U123"
    order.line_notification_consent = True
    monkeypatch.setattr(line_service.settings, "line_channel_access_token", "token")

    captured = {}

    def fake_push(user_id, message):
        captured["user_id"] = user_id
        captured["message"] = message

    monkeypatch.setattr(line_service, "_push_flex", fake_push)

    ok = await line_service.send_order_created(order)
    assert ok is True
    assert captured["user_id"] == "U123"
    assert captured["message"].alt_text == line_service._order_text(order)


async def test_send_order_created_skips_without_token(monkeypatch):
    order = _make_order()
    order.line_user_id = "U123"
    order.line_notification_consent = True
    monkeypatch.setattr(line_service.settings, "line_channel_access_token", "")
    assert await line_service.send_order_created(order) is False
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && uv run pytest tests/test_line_service.py -v`
Expected: FAIL（`AttributeError: module ... has no attribute '_flex_message'`）

- [ ] **Step 3: 替換 line_service.py 的 import 區與推播實作**

把檔案頂部的：

```python
import asyncio
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings
from app.models.order import Order

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

logger = logging.getLogger(__name__)
```

改為：

```python
import asyncio
import logging

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    PushMessageRequest,
)
from linebot.v3.messaging.exceptions import ApiException

from app.core.config import settings
from app.models.order import Order

logger = logging.getLogger(__name__)
```

- [ ] **Step 4: 替換尾端的 `_build_message` / `_post_push_message` / `send_order_created`**

把現有 `_build_message`、`_post_push_message`、`send_order_created` 三個函式整段（從 `def _build_message` 到檔案結尾）替換為：

```python
def _configuration() -> Configuration:
    return Configuration(access_token=settings.line_channel_access_token)


def _flex_message(order: Order) -> FlexMessage:
    return FlexMessage(
        alt_text=_order_text(order),
        contents=FlexContainer.from_dict(_order_flex(order)),
    )


def _push_flex(user_id: str, message: FlexMessage) -> None:
    with ApiClient(_configuration()) as api_client:
        MessagingApi(api_client).push_message(
            PushMessageRequest(to=user_id, messages=[message])
        )


async def send_order_created(order: Order) -> bool:
    if (
        not settings.line_channel_access_token
        or not order.line_user_id
        or not order.line_notification_consent
    ):
        return False

    try:
        await asyncio.to_thread(_push_flex, order.line_user_id, _flex_message(order))
    except (ApiException, OSError):
        logger.warning(
            "LINE order notification failed: order_no=%s",
            order.order_no,
            exc_info=True,
        )
        return False
    return True
```

- [ ] **Step 5: 跑測試確認通過**

Run: `cd backend && uv run pytest tests/test_line_service.py -v`
Expected: PASS（含既有 `_order_flex`／`_order_text` 測試與新推播測試）

- [ ] **Step 6: Lint 與型別**

Run: `cd backend && uv run ruff check . && uv run mypy app`
Expected: 皆通過（如 mypy 對 `FlexContainer.from_dict` 回傳型別有疑慮，於該行加 `# type: ignore[...]` 並註明原因）

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/line_service.py backend/tests/test_line_service.py
git commit -m "refactor(line): 推播改用 line-bot-sdk push_message + FlexMessage"
```

---

### Task 3: Webhook 回覆文案與事件路由

新增 C／F 回覆文案常數、postback 路由與簽章解析。

**Files:**
- Modify: `backend/app/services/line_service.py`（新增 webhook 區塊）
- Test: `backend/tests/test_line_webhook_service.py`（新檔）

**Interfaces:**
- Consumes: `settings.line_channel_secret`、`_configuration()`。
- Produces:
  - `REPORT_PAYMENT_REPLY: str`、`PURCHASE_NOTICE_REPLY: str`
  - `POSTBACK_REPLIES: dict[str, str]`
  - `_reply(reply_token: str, text: str) -> None`
  - `handle_webhook_events(body: str, signature: str) -> None`（未設 secret → 記 log 後 return；簽章不符 → 丟 `InvalidSignatureError`；只處理 `PostbackEvent`，依 `postback.data` 回覆，未知 data 略過）

- [ ] **Step 1: 寫失敗測試**

建立 `backend/tests/test_line_webhook_service.py`：

```python
import base64
import hashlib
import hmac
import json

import pytest
from linebot.v3.exceptions import InvalidSignatureError

from app.services import line_service

TEST_SECRET = "testsecret"


def _sign(secret: str, body: str) -> str:
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


def _postback_body(data: str) -> str:
    return json.dumps(
        {
            "destination": "Uxxxxxxxxxx",
            "events": [
                {
                    "type": "postback",
                    "mode": "active",
                    "timestamp": 1700000000000,
                    "source": {"type": "user", "userId": "U123"},
                    "webhookEventId": "01EXAMPLE",
                    "deliveryContext": {"isRedelivery": False},
                    "replyToken": "reply-token-123",
                    "postback": {"data": data},
                }
            ],
        }
    )


@pytest.fixture
def capture_reply(monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", TEST_SECRET)
    calls = []
    monkeypatch.setattr(line_service, "_reply", lambda token, text: calls.append((token, text)))
    return calls


def test_dispatch_report_payment(capture_reply):
    body = _postback_body("action=report_payment")
    line_service.handle_webhook_events(body, _sign(TEST_SECRET, body))
    assert capture_reply == [("reply-token-123", line_service.REPORT_PAYMENT_REPLY)]


def test_dispatch_purchase_notice(capture_reply):
    body = _postback_body("action=purchase_notice")
    line_service.handle_webhook_events(body, _sign(TEST_SECRET, body))
    assert capture_reply == [("reply-token-123", line_service.PURCHASE_NOTICE_REPLY)]


def test_unknown_postback_no_reply(capture_reply):
    body = _postback_body("action=unknown")
    line_service.handle_webhook_events(body, _sign(TEST_SECRET, body))
    assert capture_reply == []


def test_invalid_signature_raises(monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", TEST_SECRET)
    body = _postback_body("action=report_payment")
    with pytest.raises(InvalidSignatureError):
        line_service.handle_webhook_events(body, "wrong-signature")


def test_no_secret_skips(monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", "")
    calls = []
    monkeypatch.setattr(line_service, "_reply", lambda token, text: calls.append((token, text)))
    body = _postback_body("action=report_payment")
    line_service.handle_webhook_events(body, "anything")
    assert calls == []
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && uv run pytest tests/test_line_webhook_service.py -v`
Expected: FAIL（`AttributeError: ... handle_webhook_events`）

- [ ] **Step 3: 在 line_service.py 新增 webhook import**

在檔案頂部 import 區，於 messaging import 之後新增：

```python
from linebot.v3 import WebhookParser
from linebot.v3.messaging import ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import PostbackEvent
```

（`ReplyMessageRequest`、`TextMessage` 也可併入既有 `from linebot.v3.messaging import (...)` 區塊，維持字母排序以符合 ruff isort。）

- [ ] **Step 4: 新增文案常數與路由函式**

在 `send_order_created` 之後（檔案結尾）新增：

```python
REPORT_PAYMENT_REPLY = (
    "感謝您的訂購 🍐\n"
    "請依下列格式回覆，確認款項後盡快為您安排出貨：\n\n"
    "訂單編號：MM-______\n"
    "帳號末5碼：______\n"
    "匯款金額：______"
)

PURCHASE_NOTICE_REPLY = (
    "🍐 妙媽媽果園 購買須知\n\n"
    "・運費 NT$150，單筆滿 NT$5,000 免運\n"
    "・付款方式：轉帳匯款，請於下單後 3 日內完成\n"
    "・匯款後請點選「匯款回報」告知帳號末5碼與金額\n"
    "・確認款項後安排出貨\n\n"
    "有任何問題歡迎直接傳訊息給我們 😊"
)

POSTBACK_REPLIES = {
    "action=report_payment": REPORT_PAYMENT_REPLY,
    "action=purchase_notice": PURCHASE_NOTICE_REPLY,
}


def _reply(reply_token: str, text: str) -> None:
    with ApiClient(_configuration()) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


def handle_webhook_events(body: str, signature: str) -> None:
    if not settings.line_channel_secret:
        logger.warning("LINE webhook secret 未設定，略過事件處理")
        return

    parser = WebhookParser(settings.line_channel_secret)
    events = parser.parse(body, signature)
    for event in events:
        if not isinstance(event, PostbackEvent):
            continue
        reply_text = POSTBACK_REPLIES.get(event.postback.data)
        if reply_text is None or event.reply_token is None:
            continue
        try:
            _reply(event.reply_token, reply_text)
        except (ApiException, OSError):
            logger.warning(
                "LINE reply failed: data=%s", event.postback.data, exc_info=True
            )
```

> `event.reply_token is None` 的判斷一併滿足 mypy strict（reply_token 型別為 `str | None`）。`_reply` 失敗只記 log、不向上拋，避免 webhook 回 500 導致 LINE 重送。

- [ ] **Step 5: 跑測試確認通過**

Run: `cd backend && uv run pytest tests/test_line_webhook_service.py -v`
Expected: PASS（5 passed）

- [ ] **Step 6: Lint 與型別**

Run: `cd backend && uv run ruff check . && uv run mypy app`
Expected: 皆通過（`reply_token is None` 已在 Step 4 處理）。

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/line_service.py backend/tests/test_line_webhook_service.py
git commit -m "feat(line): webhook 事件路由與 C/F 回覆文案"
```

---

### Task 4: Webhook 路由端點

新增 `POST /api/line/webhook`，串接 `handle_webhook_events`，簽章不符回 400。

**Files:**
- Create: `backend/app/api/routes/line_webhook.py`
- Modify: `backend/app/main.py`（import + `include_router`）
- Test: `backend/tests/test_line_webhook_api.py`（新檔）

**Interfaces:**
- Consumes: `line_service.handle_webhook_events`、`InvalidSignatureError`。
- Produces: 路由 `POST /api/line/webhook`（200 `{"status": "ok"}`；簽章不符 400）。

- [ ] **Step 1: 寫失敗測試**

建立 `backend/tests/test_line_webhook_api.py`：

```python
import base64
import hashlib
import hmac
import json

from httpx import AsyncClient

from app.services import line_service

TEST_SECRET = "testsecret"


def _sign(secret: str, body: str) -> str:
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(mac).decode()


def _postback_body(data: str) -> str:
    return json.dumps(
        {
            "destination": "Uxxxxxxxxxx",
            "events": [
                {
                    "type": "postback",
                    "mode": "active",
                    "timestamp": 1700000000000,
                    "source": {"type": "user", "userId": "U123"},
                    "webhookEventId": "01EXAMPLE",
                    "deliveryContext": {"isRedelivery": False},
                    "replyToken": "reply-token-123",
                    "postback": {"data": data},
                }
            ],
        }
    )


async def test_webhook_valid_signature_returns_200(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", TEST_SECRET)
    monkeypatch.setattr(line_service, "_reply", lambda token, text: None)
    body = _postback_body("action=purchase_notice")
    resp = await client.post(
        "/api/line/webhook",
        content=body,
        headers={"X-Line-Signature": _sign(TEST_SECRET, body)},
    )
    assert resp.status_code == 200


async def test_webhook_invalid_signature_returns_400(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", TEST_SECRET)
    body = _postback_body("action=purchase_notice")
    resp = await client.post(
        "/api/line/webhook",
        content=body,
        headers={"X-Line-Signature": "bad-signature"},
    )
    assert resp.status_code == 400


async def test_webhook_empty_events_returns_200(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(line_service.settings, "line_channel_secret", TEST_SECRET)
    body = json.dumps({"destination": "Uxxxxxxxxxx", "events": []})
    resp = await client.post(
        "/api/line/webhook",
        content=body,
        headers={"X-Line-Signature": _sign(TEST_SECRET, body)},
    )
    assert resp.status_code == 200
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && uv run pytest tests/test_line_webhook_api.py -v`
Expected: FAIL（404，路由尚未存在）

- [ ] **Step 3: 建立路由檔**

建立 `backend/app/api/routes/line_webhook.py`：

```python
import asyncio

from fastapi import APIRouter, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.services import line_service

router = APIRouter(prefix="/api", tags=["line"])


@router.post("/line/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    signature = request.headers.get("X-Line-Signature", "")
    body = (await request.body()).decode("utf-8")
    try:
        await asyncio.to_thread(line_service.handle_webhook_events, body, signature)
    except InvalidSignatureError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc
    return {"status": "ok"}
```

- [ ] **Step 4: 在 main.py 註冊路由**

在 `backend/app/main.py` 的 import：

```python
from app.api.routes import admin_auth, admin_images, admin_orders, admin_products, orders, products
```

改為（加入 `line_webhook`）：

```python
from app.api.routes import (
    admin_auth,
    admin_images,
    admin_orders,
    admin_products,
    line_webhook,
    orders,
    products,
)
```

並在其他 `include_router` 之後新增：

```python
    app.include_router(line_webhook.router)
```

- [ ] **Step 5: 跑測試確認通過**

Run: `cd backend && uv run pytest tests/test_line_webhook_api.py -v`
Expected: PASS（3 passed）

- [ ] **Step 6: Lint 與型別**

Run: `cd backend && uv run ruff check . && uv run mypy app`
Expected: 皆通過。

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/routes/line_webhook.py backend/app/main.py backend/tests/test_line_webhook_api.py
git commit -m "feat(line): 新增 /api/line/webhook 端點"
```

---

### Task 5: Rich Menu 建立指令

新增 `build_rich_menu_request`（純函式，可測）與 `setup_rich_menu`（呼叫 API），並加 `cli.py` 子指令 `setup-richmenu`。

**Files:**
- Modify: `backend/app/services/line_service.py`（新增 rich menu 區塊）
- Modify: `backend/app/cli.py`（新增子指令）
- Create: `backend/assets/richmenu/.gitkeep`（圖片放置處；實際 PNG 另製）
- Test: `backend/tests/test_line_richmenu.py`（新檔）

**Interfaces:**
- Consumes: `settings.line_channel_access_token`、`settings.line_liff_id`、`_configuration()`。
- Produces:
  - `build_rich_menu_request(liff_id: str) -> RichMenuRequest`
  - `setup_rich_menu(image_path: str, liff_id: str) -> str`（回傳 rich_menu_id）

- [ ] **Step 1: 寫失敗測試**

建立 `backend/tests/test_line_richmenu.py`：

```python
from app.services import line_service


def test_build_rich_menu_request_layout():
    req = line_service.build_rich_menu_request("1234567890-AbcdEfgh")

    assert req.size.width == 2500
    assert req.size.height == 843
    assert req.chat_bar_text == "選單"
    assert len(req.areas) == 3

    area_a, area_c, area_f = req.areas

    assert area_a.bounds.x == 0
    assert area_a.bounds.width == 833
    assert area_a.action.uri == "https://liff.line.me/1234567890-AbcdEfgh"

    assert area_c.bounds.x == 833
    assert area_c.bounds.width == 833
    assert area_c.action.data == "action=report_payment"
    assert area_c.action.display_text == "我要回報匯款"

    assert area_f.bounds.x == 1666
    assert area_f.bounds.width == 834
    assert area_f.action.data == "action=purchase_notice"
    assert area_f.action.display_text == "購買須知"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `cd backend && uv run pytest tests/test_line_richmenu.py -v`
Expected: FAIL（`AttributeError: ... build_rich_menu_request`）

- [ ] **Step 3: 在 line_service.py 新增 rich menu import**

在 import 區的 messaging import 區塊加入（維持字母排序）：

```python
from linebot.v3.messaging import (
    MessagingApiBlob,
    PostbackAction,
    RichMenuArea,
    RichMenuBounds,
    RichMenuRequest,
    RichMenuSize,
    URIAction,
)
```

- [ ] **Step 4: 新增 rich menu 函式**

在檔案結尾新增：

```python
RICH_MENU_NAME = "妙媽媽果園選單"
RICH_MENU_CHAT_BAR_TEXT = "選單"


def build_rich_menu_request(liff_id: str) -> RichMenuRequest:
    return RichMenuRequest(
        size=RichMenuSize(width=2500, height=843),
        selected=True,
        name=RICH_MENU_NAME,
        chatBarText=RICH_MENU_CHAT_BAR_TEXT,
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                action=URIAction(label="立即訂購", uri=f"https://liff.line.me/{liff_id}"),
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=833, y=0, width=833, height=843),
                action=PostbackAction(
                    label="匯款回報",
                    data="action=report_payment",
                    displayText="我要回報匯款",
                ),
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1666, y=0, width=834, height=843),
                action=PostbackAction(
                    label="購買須知",
                    data="action=purchase_notice",
                    displayText="購買須知",
                ),
            ),
        ],
    )


def setup_rich_menu(image_path: str, liff_id: str) -> str:
    with ApiClient(_configuration()) as api_client:
        api = MessagingApi(api_client)
        blob_api = MessagingApiBlob(api_client)
        result = api.create_rich_menu(build_rich_menu_request(liff_id))
        rich_menu_id = result.rich_menu_id
        with open(image_path, "rb") as image_file:
            blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=bytearray(image_file.read()),
                _headers={"Content-Type": "image/png"},
            )
        api.set_default_rich_menu(rich_menu_id)
    return rich_menu_id
```

> 註：v3 的 pydantic 模型使用 camelCase 別名（`chatBarText`、`displayText`），以別名建構最穩。`build_rich_menu_request` 不觸網路，故可單元測試；`setup_rich_menu` 觸網路，靠手動執行驗證（見 Step 8）。

- [ ] **Step 5: 跑測試確認通過**

Run: `cd backend && uv run pytest tests/test_line_richmenu.py -v`
Expected: PASS（1 passed）

- [ ] **Step 6: 加入 cli 子指令**

在 `backend/app/cli.py`：

頂部 import 區新增：

```python
from app.core.config import settings
from app.services import line_service
```

在 `_run_create_admin` 之後新增：

```python
def _run_setup_richmenu(image: str, liff_id: str) -> None:
    if not liff_id:
        raise SystemExit("缺少 LIFF ID（請用 --liff-id 或設定 LINE_LIFF_ID）")
    if not settings.line_channel_access_token:
        raise SystemExit("缺少 LINE_CHANNEL_ACCESS_TOKEN")
    rich_menu_id = line_service.setup_rich_menu(image, liff_id)
    print(f"已建立並套用 Rich Menu：{rich_menu_id}")
```

在 `main()` 的 `sub.add_parser("seed-product", ...)` 之後新增：

```python
    richmenu = sub.add_parser("setup-richmenu", help="建立並套用 Rich Menu")
    richmenu.add_argument("--image", required=True, help="Rich Menu 圖片路徑（2500x843 PNG）")
    richmenu.add_argument("--liff-id", default=None, help="LIFF App ID（預設取 LINE_LIFF_ID）")
```

並在 `main()` 的指令分支末端新增：

```python
    elif args.command == "setup-richmenu":
        _run_setup_richmenu(args.image, args.liff_id or settings.line_liff_id)
```

- [ ] **Step 7: 建立圖片資料夾佔位 + Lint/型別/全測**

```bash
mkdir -p backend/assets/richmenu && touch backend/assets/richmenu/.gitkeep
cd backend && uv run ruff check . && uv run mypy app && uv run pytest -q
```
Expected: lint／mypy 通過，全測 PASS。

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/line_service.py backend/app/cli.py backend/tests/test_line_richmenu.py backend/assets/richmenu/.gitkeep
git commit -m "feat(line): setup-richmenu 指令建立並套用 Rich Menu"
```

> **手動驗證（非自動測試，需真實憑證與圖片）：**
> 1. 備妥 2500×843 PNG，放 `backend/assets/richmenu/richmenu-compact.png`。
> 2. 設定 `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_LIFF_ID`。
> 3. `cd backend && uv run python -m app.cli setup-richmenu --image assets/richmenu/richmenu-compact.png`
> 4. 於手機 LINE 開啟官方帳號，確認選單三格動作正確。

---

## 一次性設定（部署後，非程式碼）

- LINE Developers Console → 該 Messaging API channel：
  - Webhook URL 設為 `https://<Cloud Run 網址>/api/line/webhook`，啟用 webhook，關閉「自動回覆訊息」以免與 C／F 衝突。
- Cloud Run 環境變數：設定 `LINE_CHANNEL_SECRET`、`LINE_LIFF_ID`（`LINE_CHANNEL_SECRET` 建議掛 Secret Manager）。
- 部署後執行一次 `setup-richmenu`（見 Task 5 手動驗證）。

## 部署提醒

- 正式環境只能從 `master` 部署，合併後再部署。
- 調整運費／免運門檻時，記得同步更新 `PURCHASE_NOTICE_REPLY` 文案（與 `app/core/constants.py` 無自動連動）。
