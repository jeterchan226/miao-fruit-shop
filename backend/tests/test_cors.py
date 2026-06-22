from httpx import AsyncClient


async def test_cors_allows_vercel_preview_origin_without_trailing_slash(
    client: AsyncClient,
):
    """瀏覽器送的 Origin 不含結尾斜線，本專案的 preview 部署網址必須被放行。"""
    origin = "https://frontend-jtwn97j7c-jeterchans-projects.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_allows_vercel_production_origin(client: AsyncClient):
    origin = "https://frontend-jeterchans-projects.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_rejects_other_vercel_project(client: AsyncClient):
    """收斂後，別人的 vercel.app 專案不得被放行（避免帶 cookie 跨域）。"""
    resp = await client.get(
        "/health",
        headers={"Origin": "https://some-other-app.vercel.app"},
    )
    assert "access-control-allow-origin" not in resp.headers


async def test_cors_rejects_unknown_origin(client: AsyncClient):
    resp = await client.get(
        "/health", headers={"Origin": "https://evil.example.com"}
    )
    assert "access-control-allow-origin" not in resp.headers
