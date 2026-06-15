from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_image import ProductImage
from app.repositories import image_repo, product_repo


async def _seed_product(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


async def test_add_and_list_by_product(db_session: AsyncSession):
    p = await _seed_product(db_session)
    img = ProductImage(product_id=p.id, url="https://example.com/1.jpg", sort_order=0)
    saved = await image_repo.add(db_session, img)
    assert saved.id is not None

    imgs = await image_repo.list_by_product(db_session, p.id)
    assert len(imgs) == 1
    assert imgs[0].url == "https://example.com/1.jpg"


async def test_get_by_id_returns_none_for_missing(db_session: AsyncSession):
    assert await image_repo.get_by_id(db_session, 999999) is None


async def test_delete_removes_record(db_session: AsyncSession):
    p = await _seed_product(db_session)
    img = await image_repo.add(
        db_session, ProductImage(product_id=p.id, url="https://example.com/2.jpg")
    )
    await image_repo.delete(db_session, img)
    assert await image_repo.get_by_id(db_session, img.id) is None


async def test_list_ordered_by_sort_order(db_session: AsyncSession):
    p = await _seed_product(db_session)
    await image_repo.add(db_session, ProductImage(product_id=p.id, url="b.jpg", sort_order=2))
    await image_repo.add(db_session, ProductImage(product_id=p.id, url="a.jpg", sort_order=1))
    imgs = await image_repo.list_by_product(db_session, p.id)
    assert [i.url for i in imgs] == ["a.jpg", "b.jpg"]
