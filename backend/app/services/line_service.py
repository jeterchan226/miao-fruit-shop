import asyncio
import logging

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.messaging.exceptions import ApiException
from linebot.v3.webhooks import PostbackEvent
from urllib3.exceptions import HTTPError as Urllib3HTTPError

from app.core.config import settings
from app.models.order import Order

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
            (
                "運費: 免運費"
                if order.shipping_fee == 0
                else f"運費: NT$ {order.shipping_fee:,}"
            ),
            f"訂單合計: NT$ {order.total:,}",
            "",
            f"收件人: {order.customer_name}",
            f"電話: {order.customer_phone}",
            (
                f"地址: {order.ship_zipcode} "
                f"{order.ship_city}{order.ship_district}{order.ship_street}"
            ),
            f"希望送達: {order.preferred_date}",
            f"送達時段: {_delivery_window_label(order)}",
            "",
            "請於 3 日內完成轉帳，款項確認後將安排出貨。",
        ]
    )
    return "\n".join(lines)


BRAND_HEADER_BG = "#E89B3C"     # orange-cta
LABEL_COLOR = "#6B7D52"         # sage-700
TEXT_COLOR = "#6B4E32"          # brown-700
TOTAL_COLOR = "#4A3A2A"         # brown-800
DIVIDER_COLOR = "#E8D29E"       # cream-deep
FREE_SHIPPING_COLOR = "#3E8E41"  # green，免運費標示
BANK_BOX_BG = "#FBF3E0"         # 轉帳資訊底色（淺奶油）

# 固定店家轉帳資訊（不變）
PAYMENT_METHOD_LABEL = "轉帳匯款"
BANK_NAME = "中華郵政（代碼 700）"
BANK_BRANCH = "卓蘭郵局"
BANK_ACCOUNT_NAME = "劉芳妙"
BANK_ACCOUNT_NO = "0291377-0159424"
REMITTANCE_NOTE = "匯款完成後，請務必告知「匯款帳號末 5 碼」及「匯款金額」。"

# 送達時段顯示文字（對應 Order.delivery_window）
DELIVERY_WINDOW_LABELS = {
    "any": "不指定",
    "am": "上午 9–13",
    "pm": "下午 14–18",
}


def _delivery_window_label(order: Order) -> str:
    return DELIVERY_WINDOW_LABELS.get(order.delivery_window, order.delivery_window)


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


def _stacked_row(label: str, value: str) -> dict:
    """標籤獨立一行（靠左），內容換到下一行佔滿寬度顯示。"""
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": LABEL_COLOR},
            {"type": "text", "text": value, "size": "sm",
             "color": TEXT_COLOR, "wrap": True},
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


def _payment_rows() -> list[dict]:
    return [
        _divider(),
        {"type": "text", "text": "付款方式", "weight": "bold",
         "color": LABEL_COLOR, "size": "sm", "margin": "md"},
        {"type": "text", "text": PAYMENT_METHOD_LABEL, "size": "sm",
         "color": TEXT_COLOR},
        {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "backgroundColor": BANK_BOX_BG,
            "cornerRadius": "8px",
            "paddingAll": "12px",
            "margin": "sm",
            "contents": [
                {"type": "text", "text": BANK_NAME, "size": "sm",
                 "color": TOTAL_COLOR, "weight": "bold"},
                {"type": "text", "text": BANK_BRANCH, "size": "sm",
                 "color": TEXT_COLOR},
                {"type": "text", "text": f"戶名：{BANK_ACCOUNT_NAME}",
                 "size": "sm", "color": TEXT_COLOR},
                {"type": "text", "text": f"帳號：{BANK_ACCOUNT_NO}",
                 "size": "sm", "color": TOTAL_COLOR, "weight": "bold"},
            ],
        },
        {"type": "text", "text": REMITTANCE_NOTE, "size": "xs",
         "color": TEXT_COLOR, "wrap": True, "margin": "sm"},
    ]


def _shipping_row(order: Order) -> dict:
    if order.shipping_fee == 0:
        return _kv_row("運費", "免運費",
                       value_color=FREE_SHIPPING_COLOR, value_bold=True)
    return _kv_row("運費", f"NT$ {order.shipping_fee:,}")


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
                _shipping_row(order),
                _kv_row("訂單合計", f"NT$ {order.total:,}",
                        value_color=TOTAL_COLOR, value_bold=True),
                _divider(),
                _kv_row("收件人", order.customer_name),
                _kv_row("電話", order.customer_phone),
                _stacked_row("地址", address),
                _kv_row("希望送達", str(order.preferred_date)),
                _kv_row("送達時段", _delivery_window_label(order)),
                *_payment_rows(),
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
    except (ApiException, Urllib3HTTPError, OSError):
        logger.warning(
            "LINE order notification failed: order_no=%s",
            order.order_no,
            exc_info=True,
        )
        return False
    return True


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
