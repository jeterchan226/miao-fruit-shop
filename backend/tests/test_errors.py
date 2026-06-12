from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.errors import register_exception_handlers
from app.core.exceptions import (
    AuthError,
    InsufficientStockError,
    NotFoundError,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def not_found() -> dict[str, str]:
        raise NotFoundError("找不到商品")

    @app.get("/stock")
    async def stock() -> dict[str, str]:
        raise InsufficientStockError("庫存不足")

    @app.get("/auth")
    async def auth() -> dict[str, str]:
        raise AuthError("未授權")

    return app


async def test_not_found_maps_to_404_with_code():
    transport = ASGITransport(app=_build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/not-found")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "找不到商品", "code": "NOT_FOUND"}


async def test_insufficient_stock_maps_to_409():
    transport = ASGITransport(app=_build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/stock")
    assert resp.status_code == 409
    assert resp.json()["code"] == "INSUFFICIENT_STOCK"


async def test_auth_error_maps_to_401():
    transport = ASGITransport(app=_build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/auth")
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTH_ERROR"
