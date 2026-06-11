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
