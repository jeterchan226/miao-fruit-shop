from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_image import ProductImage


async def list_by_product(session: AsyncSession, product_id: int) -> list[ProductImage]:
    result = await session.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id, ProductImage.is_two_pack.is_(None))
        .order_by(ProductImage.sort_order, ProductImage.id)
    )
    return list(result.scalars().all())


async def list_by_group(
    session: AsyncSession, product_id: int, is_two_pack: bool
) -> list[ProductImage]:
    result = await session.execute(
        select(ProductImage)
        .where(
            ProductImage.product_id == product_id,
            ProductImage.is_two_pack == is_two_pack,
        )
        .order_by(ProductImage.sort_order, ProductImage.id)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, image_id: int) -> ProductImage | None:
    return await session.get(ProductImage, image_id)


async def add(session: AsyncSession, image: ProductImage) -> ProductImage:
    session.add(image)
    await session.flush()
    return image


async def delete(session: AsyncSession, image: ProductImage) -> None:
    await session.delete(image)
    await session.flush()
