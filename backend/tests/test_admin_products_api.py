import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.repositories import admin_repo, product_repo


async def _auth_header(session) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(username="miaomama", hashed_password=hash_password("pw"), is_active=True),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def _seed_product(session) -> Product:
    product = Product(slug="kanro", name="甘露梨", description="d", image="i", season="s")
    product.specs = [
        ProductSpec(label="A", qty_text="q", price=880, stock_qty=20, sort_order=1),
    ]
    return await product_repo.add(session, product)


@pytest.mark.parametrize(
    "method,url",
    [
        ("GET", "/api/admin/products"),
        ("PATCH", "/api/admin/products/1"),
        ("POST", "/api/admin/products/1/specs"),
        ("PATCH", "/api/admin/specs/1"),
        ("DELETE", "/api/admin/specs/1"),
    ],
)
async def test_admin_endpoints_require_auth(client: AsyncClient, method: str, url: str):
    resp = await client.request(method, url, json={})
    assert resp.status_code == 401


async def test_admin_list_includes_stock_qty(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    await _seed_product(db_session)
    resp = await client.get("/api/admin/products", headers=headers)
    assert resp.status_code == 200
    assert resp.json()[0]["specs"][0]["stock_qty"] == 20


async def test_admin_update_product(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    resp = await client.patch(
        f"/api/admin/products/{p.id}", json={"name": "新名字"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名字"


async def test_admin_update_missing_product_404(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    resp = await client.patch(
        "/api/admin/products/999999", json={"name": "x"}, headers=headers
    )
    assert resp.status_code == 404


async def test_admin_spec_create_update_delete(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    created = await client.post(
        f"/api/admin/products/{p.id}/specs",
        json={"label": "B", "qty_text": "q", "price": 1880, "stock_qty": 2},
        headers=headers,
    )
    assert created.status_code == 201
    spec_id = created.json()["id"]
    assert created.json()["stock_status"] == "low"

    patched = await client.patch(
        f"/api/admin/specs/{spec_id}", json={"price": 1900}, headers=headers
    )
    assert patched.status_code == 200
    assert patched.json()["price"] == 1900

    deleted = await client.delete(f"/api/admin/specs/{spec_id}", headers=headers)
    assert deleted.status_code == 204
