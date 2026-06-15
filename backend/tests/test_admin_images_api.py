from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.repositories import admin_repo, product_repo


async def _auth(session: AsyncSession) -> dict[str, str]:
    admin = await admin_repo.add(
        session,
        AdminUser(username="miao", hashed_password=hash_password("pw"), is_active=True),
    )
    return {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"}


async def _seed_product(session: AsyncSession) -> Product:
    p = Product(slug="kanro", name="甘露梨", description="d", season="s")
    return await product_repo.add(session, p)


async def test_sign_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/admin/uploads/sign",
        json={"filename": "img.jpg", "content_type": "image/jpeg"},
    )
    assert resp.status_code == 401


@patch("app.services.image_service.gcs_service")
async def test_sign_returns_signed_url(mock_gcs, client: AsyncClient, db_session: AsyncSession):
    mock_gcs.enabled = True
    mock_gcs.sign_upload.return_value = {
        "signed_url": "https://signed", "public_url": "https://public/img.jpg"
    }
    headers = await _auth(db_session)
    resp = await client.post(
        "/api/admin/uploads/sign",
        json={"filename": "img.jpg", "content_type": "image/jpeg"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["signed_url"] == "https://signed"


async def test_register_image_201(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    resp = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://storage.googleapis.com/b/img.jpg", "sort_order": 0},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://storage.googleapis.com/b/img.jpg"


async def test_list_images(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/img.jpg", "sort_order": 0},
        headers=headers,
    )
    resp = await client.get(f"/api/admin/products/{p.id}/images", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@patch("app.services.image_service.gcs_service")
async def test_delete_image_204(mock_gcs, client: AsyncClient, db_session: AsyncSession):
    mock_gcs.enabled = True
    mock_gcs.delete_object = lambda url: None
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    reg = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/img.jpg", "sort_order": 0},
        headers=headers,
    )
    image_id = reg.json()["id"]
    resp = await client.delete(f"/api/admin/images/{image_id}", headers=headers)
    assert resp.status_code == 204


async def test_reorder_images(client: AsyncClient, db_session: AsyncSession):
    headers = await _auth(db_session)
    p = await _seed_product(db_session)
    r1 = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/a.jpg", "sort_order": 0},
        headers=headers,
    )
    r2 = await client.post(
        f"/api/admin/products/{p.id}/images",
        json={"url": "https://gcs/b.jpg", "sort_order": 1},
        headers=headers,
    )
    id_a, id_b = r1.json()["id"], r2.json()["id"]
    resp = await client.patch(
        f"/api/admin/products/{p.id}/images/reorder",
        json={"items": [{"id": id_a, "sort_order": 1}, {"id": id_b, "sort_order": 0}]},
        headers=headers,
    )
    assert resp.status_code == 200
    urls = [i["url"] for i in resp.json()]
    assert urls == ["https://gcs/b.jpg", "https://gcs/a.jpg"]
