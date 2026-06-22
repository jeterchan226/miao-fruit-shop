import asyncio
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings
from app.models.order import Order

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

logger = logging.getLogger(__name__)


def _order_text(order: Order) -> str:
    lines = [
        f"妙媽媽果園訂單已成立: {order.order_no}",
        "",
        "訂單明細",
    ]
    for item in order.items:
        lines.append(
            f"- {item.product_name} {item.spec_label} x {item.qty}: "
            f"NT$ {item.line_total:,}"
        )
    lines.extend(
        [
            "",
            f"商品小計: NT$ {order.subtotal:,}",
            f"運費: NT$ {order.shipping_fee:,}",
            f"訂單合計: NT$ {order.total:,}",
            "",
            f"收件人: {order.customer_name}",
            f"電話: {order.customer_phone}",
            (
                f"地址: {order.ship_zipcode} "
                f"{order.ship_city}{order.ship_district}{order.ship_street}"
            ),
            f"希望送達: {order.preferred_date}",
            "",
            "請於 3 日內完成轉帳，款項確認後將安排出貨。",
        ]
    )
    return "\n".join(lines)


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


def _post_push_message(token: str, user_id: str, text: str) -> None:
    body = json.dumps(
        {
            "to": user_id,
            "messages": [{"type": "text", "text": text}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        LINE_PUSH_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10):
        return


async def send_order_created(order: Order) -> bool:
    if (
        not settings.line_channel_access_token
        or not order.line_user_id
        or not order.line_notification_consent
    ):
        return False

    try:
        await asyncio.to_thread(
            _post_push_message,
            settings.line_channel_access_token,
            order.line_user_id,
            _order_text(order),
        )
    except urllib.error.HTTPError as exc:
        logger.warning(
            "LINE order notification failed: status=%s order_no=%s",
            exc.code,
            order.order_no,
        )
        return False
    except OSError:
        logger.warning(
            "LINE order notification failed: network_error order_no=%s",
            order.order_no,
            exc_info=True,
        )
        return False
    return True
