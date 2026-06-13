from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def list_active(session: AsyncSession) -> list[Product]:
    result = await session.execute(
        select(Product).where(Product.is_active.is_(True)).order_by(Product.id)
    )
    return list(result.scalars().all())


async def list_all(session: AsyncSession) -> list[Product]:
    result = await session.execute(select(Product).order_by(Product.id))
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, product_id: int) -> Product | None:
    return await session.get(Product, product_id)


async def get_by_slug(session: AsyncSession, slug: str) -> Product | None:
    result = await session.execute(select(Product).where(Product.slug == slug))
    return result.scalar_one_or_none()


async def add(session: AsyncSession, product: Product) -> Product:
    session.add(product)
    await session.flush()
    return product
