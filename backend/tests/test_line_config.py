from app.core.config import settings


def test_linebot_sdk_importable():
    from linebot.v3 import WebhookParser  # noqa: F401


def test_settings_have_line_webhook_fields():
    assert settings.line_channel_secret == ""
    assert settings.line_liff_id == ""
