from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import IDEMPOTENCY_KEY_MAX_LENGTH
from app.core.database import get_session
from app.schemas.order import OrderCreate, OrderRead
from app.services import order_service

router = APIRouter(prefix="/api", tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(
    data: OrderCreate,
    session: SessionDep,
    idempotency_key: Annotated[
        str | None, Header(min_length=1, max_length=IDEMPOTENCY_KEY_MAX_LENGTH)
    ] = None,
) -> OrderRead:
    return await order_service.create_order(session, data, idempotency_key)
