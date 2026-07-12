from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    # eager-load items,供列表項目組出商品摘要(first_item_name / item_count),避免 N+1
    list_stmt = select(Order).options(selectinload(Order.items))

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
            Order.line_display_name.ilike(pattern),
            Order.line_user_id.ilike(pattern),
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


async def count_by_status(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(
        select(Order.status, func.count()).group_by(Order.status)
    )
    return {status: count for status, count in rows.all()}


async def summary(session: AsyncSession) -> dict[str, int]:
    """後台儀表板統計:總訂單量、總營收(排除已取消)、待出貨筆數。"""
    total_orders: int = (
        await session.execute(select(func.count()).select_from(Order))
    ).scalar_one()
    total_revenue: int = (
        await session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.status != "cancelled"
            )
        )
    ).scalar_one()
    pending_shipment: int = (
        await session.execute(
            select(func.count()).select_from(Order).where(Order.status == "ready")
        )
    ).scalar_one()
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_shipment": pending_shipment,
    }
