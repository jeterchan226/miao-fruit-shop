import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.cli import create_admin
from app.core.security import verify_password
from app.repositories import admin_repo


async def test_create_admin_persists_hashed(db_session: AsyncSession):
    admin = await create_admin(db_session, "miaomama", "s3cret-pw")
    assert admin.id is not None
    fetched = await admin_repo.get_by_username(db_session, "miaomama")
    assert fetched is not None
    assert verify_password("s3cret-pw", fetched.hashed_password)


async def test_create_admin_duplicate_raises(db_session: AsyncSession):
    await create_admin(db_session, "miaomama", "s3cret-pw")
    with pytest.raises(ValueError, match="已存在"):
        await create_admin(db_session, "miaomama", "another-pw")


async def test_create_admin_short_password_raises(db_session: AsyncSession):
    with pytest.raises(ValueError, match="至少"):
        await create_admin(db_session, "shorty", "123")
