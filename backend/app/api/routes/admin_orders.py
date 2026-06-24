from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_session
from app.schemas.order import (
    AdminOrderListResponse,
    AdminOrderRead,
    AdminOrderSummary,
    OrderStatusUpdate,
)
from app.services import admin_order_service

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-orders"],
    dependencies=[Depends(get_current_admin)],
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/orders", response_model=AdminOrderListResponse)
async def list_orders(
    session: SessionDep,
    status: str | None = Query(default=None),  # noqa: B008
    date_from: date | None = Query(default=None),  # noqa: B008
    date_to: date | None = Query(default=None),  # noqa: B008
    q: str | None = Query(default=None),  # noqa: B008
    order_no: str | None = Query(default=None),  # noqa: B008
    page: int = Query(default=1, ge=1),  # noqa: B008
    page_size: int = Query(default=20, ge=1, le=100),  # noqa: B008
) -> AdminOrderListResponse:
    return await admin_order_service.list_orders(
        session,
        status=status,
        date_from=date_from,
        date_to=date_to,
        q=q,
        order_no=order_no,
        page=page,
        page_size=page_size,
    )


# 注意:此路由須宣告於 /orders/{order_no} 之前,否則 "summary" 會被當成 order_no。
@router.get("/orders/summary", response_model=AdminOrderSummary)
async def order_summary(session: SessionDep) -> AdminOrderSummary:
    return await admin_order_service.get_summary(session)


@router.get("/orders/{order_no}", response_model=AdminOrderRead)
async def get_order(order_no: str, session: SessionDep) -> AdminOrderRead:
    return await admin_order_service.get_order_detail(session, order_no)


@router.patch("/orders/{order_no}/status", response_model=AdminOrderRead)
async def change_status(
    order_no: str, data: OrderStatusUpdate, session: SessionDep
) -> AdminOrderRead:
    return await admin_order_service.change_order_status(session, order_no, data.status)
