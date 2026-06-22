from httpx import AsyncClient


async def test_cors_allows_vercel_origin_without_trailing_slash(client: AsyncClient):
    """瀏覽器送的 Origin 不含結尾斜線，vercel.app 部署網址必須被 regex 放行。"""
    origin = "https://frontend-jtwn97j7c-jeterchans-projects.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_allows_vercel_production_origin(client: AsyncClient):
    origin = "https://miao-fruit-shop.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_rejects_unknown_origin(client: AsyncClient):
    resp = await client.get(
        "/health", headers={"Origin": "https://evil.example.com"}
    )
    assert "access-control-allow-origin" not in resp.headers
