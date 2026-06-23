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
