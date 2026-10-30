# backend/CLAUDE.md

## Commands (non-standard ones)

```bash
uv run python -m app.cli seed-product      # seed initial product (first run)
uv run python -m app.cli create-admin --username admin  # create admin user
```

Tests need a running Postgres reachable via `DATABASE_URL` (`tests/conftest.py` derives the test DB name and creates it if missing: `miao_test` in the main checkout and CI, `miao_test_<worktree>` in a linked worktree, or `TEST_DB_NAME` if set). `docker compose up db` in `backend/` starts local Postgres. CI spins up its own `postgres:16` service — mirror that DB when debugging CI-only failures.

## Strict layered structure

Each domain concept (product, order, admin, image) flows through the same four layers — do not skip a layer or reach across (e.g. routes must not import repositories directly):

```
api/routes/*.py  ->  services/*.py  ->  repositories/*.py  ->  models/*.py (SQLAlchemy)
                         |
                    schemas/*.py (Pydantic, request/response shapes)
```

Only `repositories/` touches the DB; nothing above it writes raw queries.

## CORS gotcha

CORS is unusually strict and load-bearing: `settings.cors_origins_list` is an exact-match whitelist and `cors_origin_regex` only matches this team's Vercel deployments (`frontend(-<hash>)*-jeterchans-projects.vercel.app`). If a new frontend deployment alias doesn't match the regex, it must be added to `CORS_ORIGINS` explicitly or it will be silently blocked — see comments in `app/core/config.py`.
