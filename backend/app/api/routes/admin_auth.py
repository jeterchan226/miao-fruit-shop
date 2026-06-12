from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.models.admin_user import AdminUser
from app.schemas.admin import AdminRead, Token
from app.services import auth_service

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    admin = await auth_service.authenticate(session, form.username, form.password)
    return Token(access_token=auth_service.create_token_for(admin))


@router.get("/me", response_model=AdminRead)
async def me(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> AdminUser:
    return admin
