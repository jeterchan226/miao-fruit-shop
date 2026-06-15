from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_image import ProductImage
from app.repositories import product_repo


async def _seed(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    p.images = [
        ProductImage(url="https://gcs/1.jpg", sort_order=0),
        ProductImage(url="https://gcs/2.jpg", sort_order=1),
    ]
    return await product_repo.add(session, p)


async def test_public_api_returns_images_list(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    product = resp.json()[0]
    assert product["images"] == ["https://gcs/1.jpg", "https://gcs/2.jpg"]


async def test_public_api_fallback_to_legacy_image(client: AsyncClient, db_session: AsyncSession):
    p = Product(
        slug="kanro", name="甘露梨", description="d", season="s",
        image="assets/product_5.jpg",
    )
    await product_repo.add(db_session, p)
    resp = await client.get("/api/products")
    product = resp.json()[0]
    assert product["images"] == ["assets/product_5.jpg"]


async def test_public_api_empty_images_when_no_image(client: AsyncClient, db_session: AsyncSession):
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    await product_repo.add(db_session, p)
    resp = await client.get("/api/products")
    product = resp.json()[0]
    assert product["images"] == []
