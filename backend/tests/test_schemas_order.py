import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreate


def _valid_payload(**overrides):
    payload = {
        "customer": {
            "name": "王小明",
            "phone": "0912345678",
            "email": None,
            "line_user_id": "U123",
            "line_display_name": "小明",
            "line_picture_url": "https://example.com/line.jpg",
            "line_friendship_status": "friend",
            "line_notification_consent": True,
        },
        "shipping": {
            "zipcode": "100", "city": "台北市", "district": "中正區",
            "street": "重慶南路一段 122 號", "preferred_date": "2026-10-12",
            "delivery_window": "am",
        },
        "items": [{"spec_id": 1, "qty": 2}],
        "payment_method": "transfer",
        "note": None,
        "expected_total": 3910,
    }
    payload.update(overrides)
    return payload


def test_valid_payload_parses():
    order = OrderCreate.model_validate(_valid_payload())
    assert order.items[0].spec_id == 1
    assert order.items[0].qty == 2
    assert order.customer.line_user_id == "U123"
    assert order.customer.line_notification_consent is True
    assert order.shipping.delivery_window == "am"
    assert order.expected_total == 3910


def test_empty_items_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(items=[]))


def test_qty_below_one_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(items=[{"spec_id": 1, "qty": 0}]))


def test_bad_delivery_window_rejected():
    bad = _valid_payload()
    bad["shipping"]["delivery_window"] = "midnight"
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(bad)


def test_bad_payment_method_rejected():
    # 只接受 transfer,舊的付款方式一律拒絕。
    for method in ("bitcoin", "linepay", "card", "atm", "cod"):
        with pytest.raises(ValidationError):
            OrderCreate.model_validate(_valid_payload(payment_method=method))


def test_payment_method_defaults_to_transfer():
    payload = _valid_payload()
    del payload["payment_method"]
    assert OrderCreate.model_validate(payload).payment_method == "transfer"


def test_extra_top_level_field_rejected():
    with pytest.raises(ValidationError):
        OrderCreate.model_validate(_valid_payload(hacker_price=1))
