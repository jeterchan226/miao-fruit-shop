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


def test_build_message_is_flex_with_text_alt():
    order = _make_order()
    message = line_service._build_message(order)

    assert message["type"] == "flex"
    assert message["altText"] == line_service._order_text(order)
    assert message["contents"]["type"] == "bubble"
