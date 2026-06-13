from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_spec import ProductSpec


async def get_by_id(session: AsyncSession, spec_id: int) -> ProductSpec | None:
    return await session.get(ProductSpec, spec_id)


async def add(session: AsyncSession, spec: ProductSpec) -> ProductSpec:
    session.add(spec)
    await session.flush()
    return spec
