from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.models.admin_user import AdminUser
from app.repositories import admin_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")


async def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AdminUser:
    payload = decode_access_token(token)
    try:
        admin_id = int(payload.get("sub", ""))
    except (TypeError, ValueError) as exc:
        raise AuthError("登入已失效,請重新登入") from exc
    admin = await admin_repo.get_by_id(session, admin_id)
    if admin is None or not admin.is_active:
        raise AuthError("登入已失效,請重新登入")
    return admin
