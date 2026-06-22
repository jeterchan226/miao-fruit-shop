from httpx import AsyncClient


async def test_cors_allows_vercel_preview_origin_without_trailing_slash(
    client: AsyncClient,
):
    """瀏覽器送的 Origin 不含結尾斜線，本專案的 preview 部署網址必須被放行。"""
    origin = "https://frontend-jtwn97j7c-jeterchans-projects.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_allows_production_alias(client: AsyncClient):
    """真正對外的 production 別名（隨機後綴），靠精確白名單放行。"""
    origin = "https://frontend-theta-one-22.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_allows_vercel_deploy_alias(client: AsyncClient):
    """帶 team slug 的部署別名，靠 regex 放行。"""
    origin = "https://frontend-jeterchans-projects.vercel.app"
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_allows_vercel_branch_origin(client: AsyncClient):
    """git 分支部署網址（多段 -xxx）也必須命中。"""
    origin = (
        "https://frontend-git-feat-hero-remove-carousel"
        "-jeterchans-projects.vercel.app"
    )
    resp = await client.get("/health", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


async def test_cors_rejects_other_vercel_project(client: AsyncClient):
    """收斂後，別人的 vercel.app 專案不得被放行（避免帶 cookie 跨域）。"""
    resp = await client.get(
        "/health",
        headers={"Origin": "https://some-other-app.vercel.app"},
    )
    assert "access-control-allow-origin" not in resp.headers


async def test_cors_rejects_attacker_named_project(client: AsyncClient):
    """攻擊者可註冊 frontend-* 專案名，但搶不到 team slug 後綴 → 必須被擋。"""
    for origin in (
        "https://frontend-attacker.vercel.app",
        "https://frontend-pwn-evil.vercel.app",
        "https://frontend-jeterchans-projects.vercel.app.evil.com",
    ):
        resp = await client.get("/health", headers={"Origin": origin})
        assert "access-control-allow-origin" not in resp.headers, origin


async def test_cors_rejects_unknown_origin(client: AsyncClient):
    resp = await client.get(
        "/health", headers={"Origin": "https://evil.example.com"}
    )
    assert "access-control-allow-origin" not in resp.headers
