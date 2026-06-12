from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.product import PublicProductRead
from app.services import product_service

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=list[PublicProductRead])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PublicProductRead]:
    return await product_service.list_public_products(session)
