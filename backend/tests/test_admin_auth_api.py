from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.repositories import admin_repo


async def _seed_admin(session, username="miaomama", password="s3cret-pw"):
    admin = AdminUser(
        username=username, hashed_password=hash_password(password), is_active=True
    )
    await admin_repo.add(session, admin)


async def test_login_success_returns_token(client: AsyncClient, db_session: AsyncSession):
    await _seed_admin(db_session)
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "miaomama", "password": "s3cret-pw"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_login_wrong_password_401(client: AsyncClient, db_session: AsyncSession):
    await _seed_admin(db_session)
    resp = await client.post(
        "/api/admin/auth/login",
        data={"username": "miaomama", "password": "nope"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTH_ERROR"


async def test_me_with_token_returns_admin(client: AsyncClient, db_session: AsyncSession):
    await _seed_admin(db_session)
    login = await client.post(
        "/api/admin/auth/login",
        data={"username": "miaomama", "password": "s3cret-pw"},
    )
    token = login.json()["access_token"]
    resp = await client.get(
        "/api/admin/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "miaomama"
    assert "hashed_password" not in body


async def test_me_without_token_401(client: AsyncClient):
    resp = await client.get("/api/admin/auth/me")
    assert resp.status_code == 401
