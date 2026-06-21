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
