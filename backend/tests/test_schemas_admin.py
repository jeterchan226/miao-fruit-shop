from types import SimpleNamespace

from app.schemas.admin import AdminRead, Token


def test_token_defaults_to_bearer():
    token = Token(access_token="abc")
    assert token.token_type == "bearer"


def test_admin_read_from_attributes_excludes_password():
    obj = SimpleNamespace(
        id=1, username="miaomama", is_active=True, hashed_password="secret-hash"
    )
    read = AdminRead.model_validate(obj)
    assert read.model_dump() == {"id": 1, "username": "miaomama", "is_active": True}
