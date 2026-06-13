from datetime import timedelta

import pytest

from app.core.exceptions import AuthError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed) is True
    assert verify_password("wrong-pw", hashed) is False


def test_token_roundtrip_carries_subject():
    token = create_access_token(subject=42)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"


def test_expired_token_raises_auth_error():
    token = create_access_token(subject=1, expires_delta=timedelta(minutes=-1))
    with pytest.raises(AuthError):
        decode_access_token(token)


def test_garbage_token_raises_auth_error():
    with pytest.raises(AuthError):
        decode_access_token("not-a-jwt")
