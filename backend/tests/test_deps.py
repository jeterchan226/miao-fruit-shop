from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.exceptions import AuthError
from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.repositories import admin_repo


async def _make_admin(session, active=True):
    admin = AdminUser(
        username="miaomama", hashed_password=hash_password("pw"), is_active=active
    )
    return await admin_repo.add(session, admin)


async def test_valid_token_returns_admin(db_session: AsyncSession):
    admin = await _make_admin(db_session)
    token = create_access_token(subject=admin.id)
    result = await get_current_admin(token, db_session)
    assert result.id == admin.id


async def test_garbage_token_raises(db_session: AsyncSession):
    with pytest.raises(AuthError):
        await get_current_admin("not-a-jwt", db_session)


async def test_expired_token_raises(db_session: AsyncSession):
    admin = await _make_admin(db_session)
    token = create_access_token(subject=admin.id, expires_delta=timedelta(minutes=-1))
    with pytest.raises(AuthError):
        await get_current_admin(token, db_session)


async def test_unknown_admin_id_raises(db_session: AsyncSession):
    token = create_access_token(subject=999999)
    with pytest.raises(AuthError):
        await get_current_admin(token, db_session)


async def test_inactive_admin_raises(db_session: AsyncSession):
    admin = await _make_admin(db_session, active=False)
    token = create_access_token(subject=admin.id)
    with pytest.raises(AuthError):
        await get_current_admin(token, db_session)
