from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import product_repo


async def _seed(session):
    product = Product(
        slug="kanro", name="甘露梨", description="d", image="i", season="s",
        tag="珍稀", tag_color="red",
    )
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, sort_order=1),
        ProductSpec(label="B", qty_text="q", price=1880, stock_qty=3,
                    low_stock_threshold=3, sort_order=2),
    ]
    await product_repo.add(session, product)


async def test_list_products_returns_active(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["name"] == "甘露梨"
    labels = [s["label"] for s in body[0]["specs"]]
    assert labels == ["A", "B"]


async def test_public_response_hides_stock_qty(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    resp = await client.get("/api/products")
    spec = resp.json()[0]["specs"][0]
    assert spec["stock_status"] == "in"
    assert "stock_qty" not in spec
    assert "low_stock_threshold" not in spec


async def test_list_products_empty(client: AsyncClient):
    resp = await client.get("/api/products")
    assert resp.status_code == 200
    assert resp.json() == []
