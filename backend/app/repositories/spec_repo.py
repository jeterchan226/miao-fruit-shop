from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product_spec import ProductSpec


async def get_by_id(session: AsyncSession, spec_id: int) -> ProductSpec | None:
    return await session.get(ProductSpec, spec_id)


async def get_for_update(session: AsyncSession, spec_id: int) -> ProductSpec | None:
    """以列鎖(SELECT ... FOR UPDATE)讀取規格,並一併載入所屬商品(供快照品名)。"""
    result = await session.execute(
        select(ProductSpec)
        .where(ProductSpec.id == spec_id)
        .with_for_update()
        .options(selectinload(ProductSpec.product))
    )
    return result.scalar_one_or_none()


async def add(session: AsyncSession, spec: ProductSpec) -> ProductSpec:
    session.add(spec)
    await session.flush()
    return spec
