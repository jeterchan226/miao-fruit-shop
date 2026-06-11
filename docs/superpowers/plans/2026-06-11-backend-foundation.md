# Backend Foundation Implementation Plan (Phase 1 of 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a runnable, tested FastAPI backend skeleton with config, async DB session, domain-error handling, CORS, a health endpoint, an async test harness, Alembic migrations scaffolding, and Docker — ready for the auth/products/orders phases to build on.

**Architecture:** Three-layer (Presentation `app/api` → Business `app/services` → Data access `app/repositories`) with shared `app/core` infrastructure. This phase builds only the shared foundation + the Presentation app shell; services/repositories arrive in later phases. All I/O is async (FastAPI async endpoints, SQLAlchemy 2.0 async + asyncpg).

**Tech Stack:** Python 3.13, FastAPI 0.136.3, SQLAlchemy 2.0.50 (async), asyncpg 0.31.0, Alembic 1.18.4, Pydantic 2.13.4, pydantic-settings 2.14.1, uvicorn 0.49.0, uv 0.11.19; tests with pytest 9.0.3 + pytest-asyncio 1.4.0 + httpx 0.28.1; ruff 0.15.16 + mypy 2.1.0; PostgreSQL 17 via Docker.

**Spec:** `docs/superpowers/specs/2026-06-11-backend-architecture-design.md` (sections 2, 3, 7, 8, 9). Auth/products/orders (spec sections 4–6) are later phases.

**Phase scope boundary:** This plan creates NO ORM models, NO business endpoints, NO auth. It delivers infrastructure + a `/health` endpoint + a green test suite. The first Alembic migration and the first model land in Phase 2 (auth).

---

## File Structure

All backend code lives under `backend/`. Files created in this phase:

- `backend/pyproject.toml` — uv project, pinned deps, pytest/ruff/mypy config
- `backend/.env.example` — documented environment variables (no secrets)
- `backend/.gitignore` — backend-local ignores (`.venv`, caches)
- `backend/app/__init__.py` — marks package
- `backend/app/core/__init__.py`
- `backend/app/core/config.py` — `Settings` (pydantic-settings), single `settings` instance
- `backend/app/core/database.py` — `Base`, async `engine`, `AsyncSessionLocal`, `get_session` dependency
- `backend/app/api/__init__.py`
- `backend/app/api/errors.py` — domain exception classes + `register_exception_handlers`
- `backend/app/main.py` — `create_app()` factory: CORS, error handlers, `/health`
- `backend/app/services/__init__.py` — empty (placeholder for Phase 2+)
- `backend/app/repositories/__init__.py` — empty (placeholder for Phase 2+)
- `backend/app/models/__init__.py` — empty (placeholder for Phase 2+)
- `backend/app/schemas/__init__.py` — empty (placeholder for Phase 2+)
- `backend/tests/__init__.py`
- `backend/tests/conftest.py` — async `engine`, `db_session` (rollback-per-test), `client` fixtures
- `backend/tests/test_config.py`
- `backend/tests/test_errors.py`
- `backend/tests/test_health.py`
- `backend/tests/test_db_session.py`
- `backend/alembic.ini` — Alembic config
- `backend/alembic/env.py` — async migration environment bound to `Base.metadata`
- `backend/alembic/script.py.mako` — migration template (Alembic default)
- `backend/Dockerfile` — production-style image (uv + uvicorn)
- `backend/.dockerignore`
- `backend/docker-compose.yml` — PostgreSQL 17 + api service for local dev
- `backend/README.md` — how to run dev server, tests, migrations

**Working directory:** every command below runs from `backend/` unless stated otherwise.

---

## Task 1: Initialize uv project, dependencies, and tool config

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.gitignore`
- Create: `backend/app/__init__.py`, `backend/app/core/__init__.py`, `backend/app/api/__init__.py`, `backend/app/services/__init__.py`, `backend/app/repositories/__init__.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/tests/__init__.py`

- [ ] **Step 1: Create the package directory tree and empty `__init__.py` files**

```bash
cd backend
mkdir -p app/core app/api app/services app/repositories app/models app/schemas tests
touch app/__init__.py app/core/__init__.py app/api/__init__.py \
      app/services/__init__.py app/repositories/__init__.py \
      app/models/__init__.py app/schemas/__init__.py tests/__init__.py
```

- [ ] **Step 2: Write `backend/pyproject.toml`**

```toml
[project]
name = "miao-fruit-shop-backend"
version = "0.1.0"
description = "妙媽媽果園 backend API"
requires-python = ">=3.13"
dependencies = [
    "fastapi==0.136.3",
    "uvicorn[standard]==0.49.0",
    "sqlalchemy==2.0.50",
    "asyncpg==0.31.0",
    "alembic==1.18.4",
    "pydantic==2.13.4",
    "pydantic-settings==2.14.1",
    "pyjwt==2.13.0",
    "pwdlib[argon2]==0.3.0",
    "python-multipart==0.0.32",
]

[dependency-groups]
dev = [
    "pytest==9.0.3",
    "pytest-asyncio==1.4.0",
    "httpx==0.28.1",
    "ruff==0.15.16",
    "mypy==2.1.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.13"
strict = true
plugins = ["pydantic.mypy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["app"]
```

- [ ] **Step 3: Write `backend/.gitignore`**

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
```

- [ ] **Step 4: Resolve and install dependencies**

Run: `uv sync`
Expected: creates `.venv/` and `uv.lock`, installs all deps without error. Final line resembles `Installed NN packages`.

- [ ] **Step 5: Verify the toolchain runs**

Run: `uv run python -c "import fastapi, sqlalchemy, pydantic_settings; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 6: Commit** (run from `backend/`; git finds the repo's `.git` in the parent dir)

```bash
git add pyproject.toml uv.lock .gitignore app tests
git commit -m "chore(backend): init uv project, deps, package layout"
```

---

## Task 2: Settings via pydantic-settings

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/.env.example`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_config.py`:
```python
from app.core.config import Settings


def test_cors_origins_list_splits_and_trims(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8080, https://miao.example ")
    s = Settings()
    assert s.cors_origins_list == ["http://localhost:8080", "https://miao.example"]


def test_defaults_apply(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.delenv("JWT_EXPIRE_MINUTES", raising=False)
    s = Settings()
    assert s.jwt_algorithm == "HS256"
    assert s.jwt_expire_minutes == 480
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.config'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/core/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()  # type: ignore[call-arg]
```

> Note: `cors_origins` is a comma-separated string (not `list[str]`) so plain `.env` values work without JSON encoding. `settings` is instantiated at import; tests construct their own `Settings()` after setting env vars.

- [ ] **Step 4: Write `backend/.env.example`**

```dotenv
# 連線到本機 PostgreSQL(docker-compose 的 db 服務或本機安裝)
DATABASE_URL=postgresql+asyncpg://miao:miao@localhost:5432/miao
# JWT 簽章密鑰(正式環境務必改成隨機長字串)
JWT_SECRET=change-me-in-prod
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
# 逗號分隔的允許來源
CORS_ORIGINS=http://localhost:8080
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (2 passed).

> The test sets `DATABASE_URL`/`JWT_SECRET` via `monkeypatch`, so importing `app.core.config` (which builds `settings`) succeeds even without a `.env` file present.

- [ ] **Step 6: Commit**

```bash
git add app/core/config.py .env.example tests/test_config.py
git commit -m "feat(backend): settings via pydantic-settings"
```

---

## Task 3: Async database engine, Base, and session dependency

**Files:**
- Create: `backend/app/core/database.py`

- [ ] **Step 1: Write the implementation**

`backend/app/core/database.py`:
```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM model 的共同基底;Phase 2+ 的 model 繼承它。"""


engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依賴:每個請求一個 async session。"""
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: Verify it imports**

Run: `uv run python -c "from app.core.database import Base, engine, get_session; print('ok')"`
Expected: prints `ok` (importing does not open a DB connection).

> No standalone unit test here — `get_session` and `Base` are exercised by the `db_session` fixture and its test in Task 6. This keeps the test meaningful (real session round-trip) rather than asserting on object identity.

- [ ] **Step 3: Commit**

```bash
git add app/core/database.py
git commit -m "feat(backend): async engine, Base, get_session dependency"
```

---

## Task 4: Domain errors and exception handlers

**Files:**
- Create: `backend/app/api/errors.py`
- Test: `backend/tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

`backend/tests/test_errors.py`:
```python
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.errors import (
    AuthError,
    InsufficientStockError,
    NotFoundError,
    register_exception_handlers,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.errors'`.

- [ ] **Step 3: Write minimal implementation**

`backend/app/api/errors.py`:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Business 層拋出的領域例外基底(不含 HTTP 概念)。"""

    code: str = "APP_ERROR"
    status_code: int = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class InsufficientStockError(AppError):
    code = "INSUFFICIENT_STOCK"
    status_code = 409


class InvalidStatusTransition(AppError):
    code = "INVALID_STATUS_TRANSITION"
    status_code = 409


class AuthError(AppError):
    code = "AUTH_ERROR"
    status_code = 401


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )
```

> `InvalidStatusTransition` is defined now (used in Phase 4) so the single error module is complete and Phase 4 needs no edits here.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_errors.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add app/api/errors.py tests/test_errors.py
git commit -m "feat(backend): domain errors + exception handlers"
```

---

## Task 5: App factory with CORS and health endpoint

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Write the implementation**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="妙媽媽果園 API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 2: Verify the module imports**

Run: `uv run python -c "from app.main import app; print(type(app).__name__)"`
Expected: prints `FastAPI`. (Requires `DATABASE_URL`/`JWT_SECRET` in `.env` or environment, since importing builds `settings`. If it errors on missing fields, create `backend/.env` by copying `.env.example`.)

> The behavioral test for `/health` is in Task 6, once the `client` fixture exists.

- [ ] **Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat(backend): app factory with CORS + /health"
```

---

## Task 6: Async test harness (conftest) + health and DB-session tests

**Files:**
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_health.py`
- Test: `backend/tests/test_db_session.py`

**Prerequisite:** a reachable PostgreSQL and a test database named `miao_test`. Create it once: `createdb -h localhost -U miao miao_test` (or via the docker-compose `db` in Task 8: `docker compose exec db createdb -U miao miao_test`). The test engine derives its URL from `settings.database_url` by replacing the database name with `miao_test`.

- [ ] **Step 1: Write `backend/tests/conftest.py`**

```python
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from app.core.config import settings
from app.core.database import Base, get_session
from app.main import app

# 從設定的 DATABASE_URL 推導測試 DB(把資料庫名換成 miao_test)
TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/miao_test"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
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
) -> AsyncGenerator[AsyncSession, None]:
    """每個測試一條連線 + 外層交易,測試結束 rollback,保持隔離。"""
    connection: AsyncConnection = await engine.connect()
    trans = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture(loop_scope="session")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Write `backend/tests/test_health.py`**

```python
from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 3: Write `backend/tests/test_db_session.py`**

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_db_session_executes_query(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/test_health.py tests/test_db_session.py -v`
Expected: PASS (2 passed). If you see a connection error, confirm the `miao_test` database exists and `DATABASE_URL` in `.env` points at a running PostgreSQL.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`
Expected: all tests PASS (test_config: 2, test_errors: 3, test_health: 1, test_db_session: 1).

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_health.py tests/test_db_session.py
git commit -m "test(backend): async harness, health + db-session tests"
```

---

## Task 7: Alembic async migrations scaffolding

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (empty dir, kept with `.gitkeep`)

> No migration is generated in this phase (no models yet). This task only wires Alembic to `Base.metadata` and the async engine so Phase 2 can run `alembic revision --autogenerate`.

- [ ] **Step 1: Generate the Alembic skeleton, then we overwrite env.py**

Run: `uv run alembic init -t async alembic`
Expected: creates `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`. (The `async` template gives an async-ready `env.py`; we replace it below for our settings + metadata.)

- [ ] **Step 2: Point `alembic.ini` script location and leave URL to env.py**

In `backend/alembic.ini`, ensure these lines (the rest of the generated file is fine as-is):
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
```
Remove or leave blank any `sqlalchemy.url =` line — the URL is supplied programmatically in `env.py`.

- [ ] **Step 3: Overwrite `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# Phase 2+ 會 import models 讓 autogenerate 偵測到表;此處先匯入套件。
import app.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url, poolclass=None)
    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Keep the empty versions dir under git**

```bash
touch alembic/versions/.gitkeep
```

- [ ] **Step 5: Verify Alembic loads config and metadata without error**

Run: `uv run alembic upgrade head`
Expected: connects and reports nothing to do (no versions yet) — exit code 0, no traceback. Confirms `env.py` imports `app.*` and reaches the DB. (Requires the dev DB from `.env` to be running.)

- [ ] **Step 6: Commit**

```bash
git add alembic.ini alembic/env.py alembic/script.py.mako alembic/versions/.gitkeep
git commit -m "chore(backend): async Alembic scaffolding bound to Base.metadata"
```

---

## Task 8: Docker image + docker-compose for local Postgres

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Create: `backend/docker-compose.yml`

- [ ] **Step 1: Write `backend/Dockerfile`**

```dockerfile
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv 由官方 image 複製進來
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /usr/local/bin/uv

WORKDIR /app

# 先裝相依(利用 layer cache),不裝 dev 群組
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write `backend/.dockerignore`**

```dockerignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
tests/
alembic/versions/__pycache__/
```

- [ ] **Step 3: Write `backend/docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: miao
      POSTGRES_PASSWORD: miao
      POSTGRES_DB: miao
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U miao"]
      interval: 5s
      timeout: 3s
      retries: 10

  api:
    build: .
    # 容器內連 db 服務,host 用 db 而非 localhost
    environment:
      DATABASE_URL: postgresql+asyncpg://miao:miao@db:5432/miao
      JWT_SECRET: change-me-in-prod
      CORS_ORIGINS: http://localhost:8080
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
```

- [ ] **Step 4: Build and smoke-test the stack**

Run: `docker compose up -d --build`
Then: `curl -s localhost:8000/health`
Expected: `{"status":"ok"}`.

- [ ] **Step 5: Create the test database inside the compose Postgres (for later test runs)**

Run: `docker compose exec db createdb -U miao miao_test`
Expected: no output, exit 0 (idempotent failure "already exists" is fine).

- [ ] **Step 6: Tear down**

Run: `docker compose down`
Expected: containers removed (volume `pgdata` persists).

- [ ] **Step 7: Commit**

```bash
git add Dockerfile .dockerignore docker-compose.yml
git commit -m "chore(backend): Dockerfile + compose (postgres 17 + api)"
```

---

## Task 9: Backend README (dev runbook)

**Files:**
- Create: `backend/README.md`

- [ ] **Step 1: Write `backend/README.md`**

````markdown
# 妙媽媽果園 Backend

FastAPI + SQLAlchemy(async)+ PostgreSQL，三層架構。詳見
`docs/superpowers/specs/2026-06-11-backend-architecture-design.md`。

## 開發環境

```bash
cd backend
cp .env.example .env          # 視需要調整連線/密鑰
uv sync                       # 安裝相依
```

啟動本機 PostgreSQL(擇一):
- 用 compose:`docker compose up -d db`
- 或本機已裝 PostgreSQL 17

建立測試資料庫(一次性):
```bash
docker compose exec db createdb -U miao miao_test   # 用 compose 時
# 或本機:createdb -h localhost -U miao miao_test
```

## 跑起來

```bash
uv run uvicorn app.main:app --reload --port 8000
curl localhost:8000/health      # {"status":"ok"}
```

## 測試 / 品質

```bash
uv run pytest -v       # 測試
uv run ruff check .    # lint
uv run mypy app        # 型別檢查
```

## 資料庫遷移(Alembic)

```bash
uv run alembic revision --autogenerate -m "描述"   # 產生遷移(Phase 2 起)
uv run alembic upgrade head                         # 套用
```

## 全棧容器

```bash
docker compose up -d --build    # db + api
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(backend): dev runbook README"
```

---

## Definition of Done (Phase 1)

- [ ] `uv run pytest -v` → 7 tests pass (config 2, errors 3, health 1, db-session 1).
- [ ] `uv run ruff check .` → clean.
- [ ] `uv run mypy app` → clean.
- [ ] `uv run uvicorn app.main:app` + `curl localhost:8000/health` → `{"status":"ok"}`.
- [ ] `docker compose up -d --build` brings up db + api; `/health` responds.
- [ ] `uv run alembic upgrade head` runs without error (no versions yet).
- [ ] All work committed.

## Next phase

Phase 2 (Admin Auth): `admin_users` model + first Alembic migration, `pwdlib` password hashing, JWT issue/verify in `core/security.py`, `POST /api/admin/auth/login`, `get_current_admin` dependency, `GET /api/admin/auth/me`. Will be planned in its own document after Phase 1 is implemented and verified.
