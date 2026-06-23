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


def _find_text_node(node, text):
    """找出 text 等於指定字串的 text node dict（找不到回 None）。"""
    if isinstance(node, dict):
        if node.get("type") == "text" and node.get("text") == text:
            return node
        for value in node.values():
            found = _find_text_node(value, text)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_text_node(value, text)
            if found is not None:
                return found
    return None


def test_bank_transfer_constants_match_expected():
    # 固定店家帳號（核對自 LINE 訂單通知圖）
    assert line_service.BANK_ACCOUNT_NO == "0291377-0159424"
    assert line_service.BANK_ACCOUNT_NAME == "劉芳妙"
    assert line_service.BANK_BRANCH == "卓蘭郵局"


def test_order_flex_free_shipping_shows_green_label():
    order = _make_order()  # shipping_fee=0
    flex = line_service._order_flex(order)

    texts = _all_text(flex)
    assert "免運費" in texts
    assert "NT$ 0" not in "\n".join(texts)  # 免運不顯示 0 元

    node = _find_text_node(flex, "免運費")
    assert node is not None
    assert node["color"] == line_service.FREE_SHIPPING_COLOR


def test_order_flex_paid_shipping_shows_amount():
    order = _make_order()
    order.shipping_fee = 150
    order.total = order.subtotal + 150
    flex = line_service._order_flex(order)

    joined = "\n".join(_all_text(flex))
    assert "NT$ 150" in joined
    assert "免運費" not in joined


def test_order_flex_includes_bank_transfer_info():
    order = _make_order()
    joined = "\n".join(_all_text(line_service._order_flex(order)))

    assert line_service.PAYMENT_METHOD_LABEL in joined  # 轉帳匯款
    assert line_service.BANK_NAME in joined
    assert line_service.BANK_BRANCH in joined
    assert f"戶名：{line_service.BANK_ACCOUNT_NAME}" in joined
    assert f"帳號：{line_service.BANK_ACCOUNT_NO}" in joined
    assert "末 5 碼" in joined  # 匯款提醒語


def test_order_flex_address_is_stacked_full_width():
    """地址改為上下兩行：標籤獨立一行、內容換到下一行佔滿寬度（非 baseline 並排）。"""
    order = _make_order()
    flex = line_service._order_flex(order)

    label_node = _find_text_node(flex, "地址")
    addr_node = _find_text_node(flex, "100 台北市中正區忠孝東路一段1號")
    assert label_node is not None
    assert addr_node is not None
    # 地址內容不再靠右對齊（堆疊版面無 align=end）
    assert addr_node.get("align") != "end"


def test_order_flex_shows_delivery_window_label():
    order = _make_order()  # delivery_window="any"
    joined = "\n".join(_all_text(line_service._order_flex(order)))
    assert "送達時段" in joined
    assert "不指定" in joined

    order.delivery_window = "am"
    joined_am = "\n".join(_all_text(line_service._order_flex(order)))
    assert "上午 9–13" in joined_am

    order.delivery_window = "pm"
    joined_pm = "\n".join(_all_text(line_service._order_flex(order)))
    assert "下午 14–18" in joined_pm


def test_order_text_includes_delivery_window():
    order = _make_order()
    order.delivery_window = "am"
    text = line_service._order_text(order)
    assert "送達時段: 上午 9–13" in text


def test_order_text_free_shipping_label():
    order = _make_order()  # shipping_fee=0
    text = line_service._order_text(order)

    assert "免運費" in text
    assert "運費: NT$ 0" not in text
