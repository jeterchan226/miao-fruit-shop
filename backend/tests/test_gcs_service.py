import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.gcs_service import GcsService


def _fake_credentials_b64() -> str:
    info = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return base64.b64encode(json.dumps(info).encode()).decode()


def _make_service(bucket: str = "test-bucket", b64: str | None = None) -> GcsService:
    return GcsService(bucket_name=bucket, credentials_b64=b64 or _fake_credentials_b64())


def test_gcs_service_disabled_when_no_credentials():
    svc = GcsService(bucket_name="", credentials_b64="")
    assert not svc.enabled


def test_gcs_service_enabled_with_credentials():
    svc = _make_service()
    assert svc.enabled


def test_make_blob_name_format():
    svc = _make_service()
    name = svc._make_blob_name(product_id=3, filename="photo.jpg")
    assert name.startswith("products/3/")
    assert name.endswith(".jpg")


def test_public_url_format():
    svc = _make_service(bucket="my-bucket")
    assert svc.public_url("products/3/abc.jpg") == (
        "https://storage.googleapis.com/my-bucket/products/3/abc.jpg"
    )


@patch("app.services.gcs_service.storage.Client")
@patch("app.services.gcs_service.service_account.Credentials.from_service_account_info")
def test_sign_returns_signed_url_and_public_url(mock_creds, mock_client_cls):
    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client_cls.return_value.bucket.return_value = mock_bucket

    svc = _make_service()
    result = svc.sign_upload(product_id=1, filename="img.jpg", content_type="image/jpeg")

    assert result["signed_url"] == "https://storage.googleapis.com/signed"
    assert result["public_url"].startswith("https://storage.googleapis.com/test-bucket/products/1/")
    mock_blob.generate_signed_url.assert_called_once()


@patch("app.services.gcs_service.storage.Client")
@patch("app.services.gcs_service.service_account.Credentials.from_service_account_info")
def test_delete_calls_blob_delete(mock_creds, mock_client_cls):
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client_cls.return_value.bucket.return_value = mock_bucket

    svc = _make_service(bucket="my-bucket")
    svc.delete_object("https://storage.googleapis.com/my-bucket/products/1/abc.jpg")

    mock_blob.delete.assert_called_once()
