import os
import re
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import Base, get_session
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_test_db_name(repo_root: Path) -> str:
    """TEST_DB_NAME 優先;linked worktree(.git 是檔案)各用一個 DB;其餘(含 CI)用 miao_test。"""
    if override := os.environ.get("TEST_DB_NAME"):
        return override
    if not (repo_root / ".git").is_file():
        return "miao_test"
    slug = re.sub(r"[^a-z0-9]+", "_", repo_root.name.lower()).strip("_")[:40]
    return f"miao_test_{slug}"


# 從設定的 DATABASE_URL 推導測試 DB(只換資料庫名,保留 driver/帳密/查詢參數)
_BASE_URL = make_url(settings.sqlalchemy_database_url)
TEST_DB_NAME = resolve_test_db_name(REPO_ROOT)
TEST_DATABASE_URL = _BASE_URL.set(database=TEST_DB_NAME).render_as_string(hide_password=False)


async def ensure_test_database() -> None:
    """測試 DB 不存在就建立;CREATE DATABASE 不能在交易內,故用 AUTOCOMMIT 連 postgres 維護庫。"""
    admin = create_async_engine(_BASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT")
    quoted = admin.dialect.identifier_preparer.quote(TEST_DB_NAME)
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
            )
            if not exists:
                await conn.execute(text(f"CREATE DATABASE {quoted}"))
    finally:
        await admin.dispose()


@pytest.fixture(autouse=True)
def no_real_line_push(monkeypatch: pytest.MonkeyPatch) -> None:
    """測試不帶 LINE token,避免本機 .env 的 token 真的呼叫 LINE;需要的測試自行 monkeypatch。"""
    monkeypatch.setattr(settings, "line_channel_access_token", "")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    await ensure_test_database()
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    """每個測試一條連線 + 外層交易,測試結束 rollback,保持隔離。"""
    connection: AsyncConnection = await engine.connect()
    trans = await connection.begin()
    session = AsyncSession(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture(loop_scope="session")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient]:
    async def _override_get_session() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        del app.dependency_overrides[get_session]
