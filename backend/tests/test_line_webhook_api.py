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
