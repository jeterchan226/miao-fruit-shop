from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import create_access_token, verify_password
from app.models.admin_user import AdminUser
from app.repositories import admin_repo


async def authenticate(
    session: AsyncSession, username: str, password: str
) -> AdminUser:
    admin = await admin_repo.get_by_username(session, username)
    if (
        admin is None
        or not admin.is_active
        or not verify_password(password, admin.hashed_password)
    ):
        raise AuthError("帳號或密碼錯誤")
    return admin


def create_token_for(admin: AdminUser) -> str:
    return create_access_token(subject=admin.id)
