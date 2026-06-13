from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service

router = APIRouter(prefix="/api", tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(data: OrderCreate, session: SessionDep) -> OrderRead:
    return await order_service.create_order(session, data)
