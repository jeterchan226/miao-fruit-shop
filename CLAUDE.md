# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

妙媽媽果園 (miao-fruit-shop) — LINE LIFF 訂購網站。前端單一商品（甘露梨）+ 多規格呈現，付款採轉帳匯款，訂單透過 LINE Messaging API 推送 Flex Message 通知。後台管理商品規格與訂單。

Backend (`backend/`), frontend (`frontend/`) and Terraform (`terraform/`) each have their own CLAUDE.md with area-specific rules.

### Backend (`backend/`, Python 3.13 + FastAPI, package manager: `uv`)

```bash
cd backend
uv sync                              # install deps (incl. dev group)
uv run uvicorn app.main:app --reload --port 8000   # dev server
uv run pytest -q                     # run all tests
uv run pytest tests/test_order_service.py -q       # single test file
uv run pytest tests/test_order_service.py::test_name -q  # single test
uv run ruff check .                  # lint
uv run mypy app                      # type check (strict)
uv run alembic upgrade head          # apply migrations
uv run alembic revision --autogenerate -m "..."     # new migration
uv run python -m app.cli seed-product      # seed initial product (first run)
uv run python -m app.cli create-admin --username admin  # create admin user
```

Tests need a running Postgres reachable via `DATABASE_URL` (test DB name is derived by swapping the DB name to `miao_test`, see `tests/conftest.py`). `docker compose up db` in `backend/` starts local Postgres. CI spins up its own `postgres:16` service — mirror that DB when debugging CI-only failures.

### Frontend (`frontend/`, React 18 + Vite 8)

```bash
cd frontend
npm install
npm run dev        # dev server, http://localhost:8080
npm run build       # -> frontend/dist
npm run preview
npm run test        # vitest run
```

### Root

`vercel.json` drives the Vercel build (`npm install --prefix frontend`, `npm run build --prefix frontend`, output `frontend/dist`, SPA rewrites). There is no root install step beyond that.

## Architecture

### Backend: strict layered structure

Each domain concept (product, order, admin, image) flows through the same four layers — do not skip a layer or reach across (e.g. routes must not import repositories directly):

```
api/routes/*.py  ->  services/*.py  ->  repositories/*.py  ->  models/*.py (SQLAlchemy)
                         |
                    schemas/*.py (Pydantic, request/response shapes)
```

- `api/routes/` — thin FastAPI routers, one per concern (`products`, `orders`, `admin_auth`, `admin_products`, `admin_orders`, `admin_images`, `line_webhook`). Depend on `core.database.get_session` for an `AsyncSession`.
- `services/` — business logic (e.g. `order_service`, `line_service` for Flex Message notifications, `gcs_service`/`image_service` for product images).
- `repositories/` — all DB access via SQLAlchemy 2.0 async; nothing above this layer writes raw queries.
- `core/` — `config.py` (pydantic-settings `Settings`, env-driven), `database.py` (engine/session/`Base`), `security.py` (JWT + argon2 for admin auth), `constants.py`, `exceptions.py`.
- `app/main.py` — `create_app()` wires CORS, exception handlers, and all routers; module-level `app` is the ASGI entrypoint.
- `cli.py` — `python -m app.cli` management commands (seed product, create admin).

CORS is unusually strict and load-bearing: `settings.cors_origins_list` is an exact-match whitelist and `cors_origin_regex` only matches this team's Vercel deployments (`frontend(-<hash>)*-jeterchans-projects.vercel.app`). If a new frontend deployment alias doesn't match the regex, it must be added to `CORS_ORIGINS` explicitly or it will be silently blocked — see comments in `backend/app/core/config.py`.

### Frontend: single product, multi-spec — not multi-product

The shop is architecturally locked to one product (甘露梨) rendered as multiple `SpecCard`s (see [MEMORY: 單一商品多規格]). Don't introduce a multi-product catalog abstraction unless explicitly asked.

- `App.jsx` — top-level state: cart, tweaks (live-editable UI theme via `TweaksPanel`), product loading from `listProducts()` in `api.js`.
- `SpecCard.jsx` — one product spec (qty/price/2-pack flag), drives `addToCart`.
- `Cart.jsx` — cart drawer; order submission currently calls a stub in `api.js` (order-placement backend integration is in progress — see project memory on order backend API).
- `AdminApp.jsx` — separate admin UI entrypoint (spec/order management, drag-sort via `@dnd-kit`).
- `useOrderNotifications.js` / `notifications.js` / `chime.js` — admin-side polling/alerting for new orders.
- `line.js` — LINE LIFF integration (identity + order context inside LINE).
- `pricing.js` — pricing/shipping calculation logic, has its own `pricing.test.js`.

Target device baseline for the storefront is iPadOS 15 Safari/WebKit — avoid `transparent` in gradients and keep first-load images light (see project memory on frontend target).

### Infrastructure

GCP resources (Cloud Run service + migrate job, Cloud SQL, GCS bucket, Secret Manager, Artifact Registry, IAM) exist in production but are not managed by any IaC in this repo; change them with `gcloud`/Console directly; `backend/deploy.sh` still owns code deploys. LINE credentials and `db-password`/`jwt-secret` are Secret Manager secrets; the Cloud SQL `miao_app` password must stay in sync with `db-password` (see project memory on Cloud SQL password sync).

### Deployment
## Deployment

- Frontend: Vercel, built from root `vercel.json`. LIFF endpoint is bound to a fixed Vercel production URL.
- Backend: GCP Cloud Run, built from `backend/Dockerfile`. DB is Cloud SQL Postgres in production, docker-compose Postgres locally.
- Production deploys only ever come from `master`; confirm changes are merged to `master` before deploying either side.
- CI (`.github/workflows/ci.yml`) runs backend pytest + mypy (blocking) against a Postgres 16 service container, and a frontend job that runs vitest (`npm test`) then the build check. There is no CD — deploys are manual (`gcloud`/`vercel`), not automated on merge.

## Docs

Feature workflow: `/to-spec` → `/work-on-ticket #NN` → `/review-and-fix <PR>`.

- **`/to-spec` in this repo follows `docs/agents/to-spec.md`**, which overrides the global skill's template: it writes an OpenSpec change (`openspec/changes/<change-id>/`, pushed on branch `spec/<change-id>`) plus a GitHub ticket pointing at it.
- `/work-on-ticket` implements from the ticket + that change, archives the change into `openspec/specs/` (the current requirements), and records progress.
- `docs/progress/` is the cross-session development memory: `STATUS.md` (snapshot) and `tickets/NN-<change-id>.md` (per-ticket log). Format and rules in `docs/progress/README.md`. Read `STATUS.md` before starting work on a ticket.

`docs/superpowers/plans/` and `docs/superpowers/specs/` hold dated per-feature plan/design docs from before OpenSpec (one pair per feature, e.g. `2026-06-11-backend-foundation.md` + matching spec). When completing a task tracked in one of these plans, mark its checkbox `- [x]` and commit.

## Response Rule：
- 直接給結果，不要前言、不要總結
- 使用工具後，只回報結果，不描述過程
- 除非我主動問，否則不解釋你在做什麼
- 程式碼和資料維持完整精確，只壓縮自然語言

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`jeterchan226/miao-fruit-shop`), via the GitHub MCP server (`mcp__github-jeterchan226__*`), not the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.
