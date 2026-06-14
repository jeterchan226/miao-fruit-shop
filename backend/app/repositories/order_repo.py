from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


async def add(session: AsyncSession, order: Order) -> Order:
    session.add(order)
    await session.flush()
    return order


async def get_by_order_no(session: AsyncSession, order_no: str) -> Order | None:
    result = await session.execute(select(Order).where(Order.order_no == order_no))
    return result.scalar_one_or_none()


async def list_filtered(
    session: AsyncSession,
    *,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    order_no: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Order]]:
    count_stmt = select(func.count()).select_from(Order)
    list_stmt = select(Order)

    if status is not None:
        count_stmt = count_stmt.where(Order.status == status)
        list_stmt = list_stmt.where(Order.status == status)
    if date_from is not None:
        count_stmt = count_stmt.where(Order.created_at >= date_from)
        list_stmt = list_stmt.where(Order.created_at >= date_from)
    if date_to is not None:
        boundary = date_to + timedelta(days=1)
        count_stmt = count_stmt.where(Order.created_at < boundary)
        list_stmt = list_stmt.where(Order.created_at < boundary)
    if q is not None:
        pattern = f"%{q}%"
        condition = or_(
            Order.customer_name.ilike(pattern),
            Order.customer_phone.ilike(pattern),
        )
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)
    if order_no is not None:
        count_stmt = count_stmt.where(Order.order_no == order_no)
        list_stmt = list_stmt.where(Order.order_no == order_no)

    total: int = (await session.execute(count_stmt)).scalar_one()
    rows = await session.execute(
        list_stmt.order_by(Order.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    return total, list(rows.scalars().all())
