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


PRODUCT_REQUIRED_FIELDS = ["name", "description", "season", "is_active"]
SPEC_REQUIRED_FIELDS = [
    "label",
    "qty_text",
    "price",
    "stock_qty",
    "low_stock_threshold",
    "sort_order",
    "is_active",
    "is_two_pack",
]


async def _admin_product(client: AsyncClient, headers: dict[str, str]) -> dict:
    return (await client.get("/api/admin/products", headers=headers)).json()[0]


@pytest.mark.parametrize("field", PRODUCT_REQUIRED_FIELDS)
async def test_update_product_required_field_null_is_422(
    client: AsyncClient, db_session: AsyncSession, field: str
):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    before = await _admin_product(client, headers)
    resp = await client.patch(f"/api/admin/products/{p.id}", json={field: None}, headers=headers)
    assert resp.status_code == 422
    assert await _admin_product(client, headers) == before


async def test_update_product_null_with_valid_field_writes_nothing(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    before = await _admin_product(client, headers)
    # 同一請求帶合法欄位,整筆 PATCH 仍應被拒、不部分寫入
    resp = await client.patch(
        f"/api/admin/products/{p.id}",
        json={"season": "不該寫入", "name": None},
        headers=headers,
    )
    assert resp.status_code == 422
    assert await _admin_product(client, headers) == before


@pytest.mark.parametrize("field", ["image", "tag", "tag_color"])
async def test_update_product_explicit_null_clears_optional_field(
    client: AsyncClient, db_session: AsyncSession, field: str
):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    p.tag = "當季"
    p.tag_color = "#fff"
    await db_session.flush()
    columns = ("name", "description", "image", "season", "tag", "tag_color", "is_active")
    before = {c: getattr(p, c) for c in columns}
    resp = await client.patch(f"/api/admin/products/{p.id}", json={field: None}, headers=headers)
    assert resp.status_code == 200
    await db_session.refresh(p)
    assert {c: getattr(p, c) for c in columns} == {**before, field: None}


@pytest.mark.parametrize("field", SPEC_REQUIRED_FIELDS)
async def test_update_spec_required_field_null_is_422(
    client: AsyncClient, db_session: AsyncSession, field: str
):
    headers = await _auth_header(db_session)
    await _seed_product(db_session)
    before = await _admin_product(client, headers)
    resp = await client.patch(
        f"/api/admin/specs/{before['specs'][0]['id']}", json={field: None}, headers=headers
    )
    assert resp.status_code == 422
    assert await _admin_product(client, headers) == before


async def test_update_spec_null_with_valid_field_writes_nothing(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    await _seed_product(db_session)
    before = await _admin_product(client, headers)
    # 同一請求帶合法欄位,整筆 PATCH 仍應被拒、不部分寫入
    resp = await client.patch(
        f"/api/admin/specs/{before['specs'][0]['id']}",
        json={"stock_qty": 1, "price": None},
        headers=headers,
    )
    assert resp.status_code == 422
    assert await _admin_product(client, headers) == before


async def test_update_spec_explicit_null_clears_note(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _auth_header(db_session)
    p = await _seed_product(db_session)
    p.specs[0].note = "備註"
    await db_session.flush()
    before = (await _admin_product(client, headers))["specs"][0]
    assert before["note"] == "備註"
    resp = await client.patch(
        f"/api/admin/specs/{before['id']}", json={"note": None}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json() == {**before, "note": None}
    assert (await _admin_product(client, headers))["specs"][0] == {**before, "note": None}
