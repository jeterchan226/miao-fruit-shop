from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_spec import ProductSpec
from app.repositories import product_repo, spec_repo
from app.schemas.product import (
    AdminProductRead,
    AdminSpecRead,
    ProductUpdate,
    PublicProductRead,
    PublicSpecRead,
    SpecCreate,
    SpecUpdate,
)


def derive_stock_status(stock_qty: int, low_stock_threshold: int) -> str:
    if stock_qty <= 0:
        return "out"
    if stock_qty <= low_stock_threshold:
        return "low"
    return "in"


def _group_images(images: list[ProductImage], is_two_pack: bool) -> list[str]:
    return [img.url for img in images if img.is_two_pack == is_two_pack]


def _to_public_spec(s: ProductSpec, product_images: list[ProductImage]) -> PublicSpecRead:
    return PublicSpecRead(
        id=s.id,
        label=s.label,
        qty_text=s.qty_text,
        price=s.price,
        stock_status=derive_stock_status(s.stock_qty, s.low_stock_threshold),
        note=s.note,
        images=_group_images(product_images, s.is_two_pack),
        is_two_pack=s.is_two_pack,
    )


def _to_admin_spec(s: ProductSpec, product_images: list[ProductImage]) -> AdminSpecRead:
    return AdminSpecRead(
        id=s.id,
        label=s.label,
        qty_text=s.qty_text,
        price=s.price,
        stock_status=derive_stock_status(s.stock_qty, s.low_stock_threshold),
        note=s.note,
        stock_qty=s.stock_qty,
        low_stock_threshold=s.low_stock_threshold,
        sort_order=s.sort_order,
        is_active=s.is_active,
        images=_group_images(product_images, s.is_two_pack),
        is_two_pack=s.is_two_pack,
    )


def _get_images(p: Product) -> list[str]:
    if p.images:
        return [img.url for img in p.images]
    if p.image:
        return [p.image]
    return []


def _to_public_product(p: Product) -> PublicProductRead:
    return PublicProductRead(
        id=p.id,
        slug=p.slug,
        name=p.name,
        description=p.description,
        images=_get_images(p),
        season=p.season,
        tag=p.tag,
        tag_color=p.tag_color,
        specs=[_to_public_spec(s, p.images) for s in p.specs if s.is_active],
    )


def _to_admin_product(p: Product) -> AdminProductRead:
    return AdminProductRead(
        id=p.id,
        slug=p.slug,
        name=p.name,
        description=p.description,
        images=_get_images(p),
        season=p.season,
        tag=p.tag,
        tag_color=p.tag_color,
        is_active=p.is_active,
        specs=[_to_admin_spec(s, p.images) for s in p.specs],
    )


async def list_public_products(session: AsyncSession) -> list[PublicProductRead]:
    products = await product_repo.list_active(session)
    return [_to_public_product(p) for p in products]


async def list_admin_products(session: AsyncSession) -> list[AdminProductRead]:
    products = await product_repo.list_all(session)
    return [_to_admin_product(p) for p in products]


async def update_product(
    session: AsyncSession, product_id: int, data: ProductUpdate
) -> AdminProductRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return _to_admin_product(product)


async def create_spec(
    session: AsyncSession, product_id: int, data: SpecCreate
) -> AdminSpecRead:
    product = await product_repo.get_by_id(session, product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    # product 可能已存在於 session identity map 中(例如同一 session 先前
    # add() 過),此時 session.get() 不會重新查詢,selectin 也就不會觸發,
    # images 會是 unloaded 狀態 —— 直接存取會在 async 下觸發不安全的 lazy load。
    # 明確 refresh 該欄位以確保安全且拿到最新資料。
    await session.refresh(product, attribute_names=["images"])
    spec = ProductSpec(product_id=product_id, **data.model_dump())
    await spec_repo.add(session, spec)
    await session.commit()
    await session.refresh(spec)
    return _to_admin_spec(spec, product.images)


async def update_spec(
    session: AsyncSession, spec_id: int, data: SpecUpdate
) -> AdminSpecRead:
    spec = await spec_repo.get_by_id(session, spec_id)
    if spec is None:
        raise NotFoundError("找不到規格")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    await session.commit()
    await session.refresh(spec)
    product = await product_repo.get_by_id(session, spec.product_id)
    if product is None:
        raise NotFoundError("找不到商品")
    await session.refresh(product, attribute_names=["images"])
    return _to_admin_spec(spec, product.images)


async def soft_delete_spec(session: AsyncSession, spec_id: int) -> None:
    spec = await spec_repo.get_by_id(session, spec_id)
    if spec is None:
        raise NotFoundError("找不到規格")
    spec.is_active = False
    await session.commit()


async def delete_spec(session: AsyncSession, spec_id: int) -> None:
    spec = await spec_repo.get_by_id(session, spec_id)
    if spec is None:
        raise NotFoundError("找不到規格")
    await spec_repo.delete(session, spec)
    await session.commit()
