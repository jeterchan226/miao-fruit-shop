from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.repositories import admin_repo


async def test_add_then_get_by_username_and_id(db_session: AsyncSession):
    admin = AdminUser(username="miaomama", hashed_password="h", is_active=True)
    saved = await admin_repo.add(db_session, admin)
    assert saved.id is not None

    by_name = await admin_repo.get_by_username(db_session, "miaomama")
    assert by_name is not None and by_name.id == saved.id

    by_id = await admin_repo.get_by_id(db_session, saved.id)
    assert by_id is not None and by_id.username == "miaomama"


async def test_get_by_username_missing_returns_none(db_session: AsyncSession):
    assert await admin_repo.get_by_username(db_session, "nobody") is None
