from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser


async def get_by_username(session: AsyncSession, username: str) -> AdminUser | None:
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == username)
    )
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, admin_id: int) -> AdminUser | None:
    return await session.get(AdminUser, admin_id)


async def add(session: AsyncSession, admin: AdminUser) -> AdminUser:
    session.add(admin)
    await session.flush()
    return admin
