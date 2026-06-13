import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_access_token, hash_password
from app.models.admin_user import AdminUser
from app.repositories import admin_repo
from app.services import auth_service


async def _make_admin(session, username="miaomama", password="s3cret-pw", active=True):
    admin = AdminUser(
        username=username, hashed_password=hash_password(password), is_active=active
    )
    return await admin_repo.add(session, admin)


async def test_authenticate_success_returns_admin(db_session: AsyncSession):
    await _make_admin(db_session)
    admin = await auth_service.authenticate(db_session, "miaomama", "s3cret-pw")
    assert admin.username == "miaomama"


async def test_authenticate_wrong_password_raises(db_session: AsyncSession):
    await _make_admin(db_session)
    with pytest.raises(AuthError):
        await auth_service.authenticate(db_session, "miaomama", "wrong")


async def test_authenticate_unknown_user_raises(db_session: AsyncSession):
    with pytest.raises(AuthError):
        await auth_service.authenticate(db_session, "ghost", "whatever")


async def test_authenticate_inactive_raises(db_session: AsyncSession):
    await _make_admin(db_session, username="disabled", active=False)
    with pytest.raises(AuthError):
        await auth_service.authenticate(db_session, "disabled", "s3cret-pw")


async def test_create_token_for_encodes_admin_id(db_session: AsyncSession):
    admin = await _make_admin(db_session)
    token = auth_service.create_token_for(admin)
    assert decode_access_token(token)["sub"] == str(admin.id)
