# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

妙媽媽果園 (miao-fruit-shop) — LINE LIFF 訂購網站。前端單一商品（甘露梨）+ 多規格呈現，付款採轉帳匯款，訂單透過 LINE Messaging API 推送 Flex Message 通知。後台管理商品規格與訂單。

Backend (`backend/`), frontend (`frontend/`) and Terraform (`terraform/`) each have their own CLAUDE.md with area-specific rules.

## Deployment

- Frontend: Vercel, built from root `vercel.json`. LIFF endpoint is bound to a fixed Vercel production URL.
- Backend: GCP Cloud Run, built from `backend/Dockerfile`. DB is Cloud SQL Postgres in production, docker-compose Postgres locally.
- Production deploys only ever come from `master`; confirm changes are merged to `master` before deploying either side.
- CI (`.github/workflows/ci.yml`) runs backend pytest + non-blocking mypy against a Postgres 16 service container, and a frontend job that runs vitest (`npm test`) then the build check. There is no CD — deploys are manual (`gcloud`/`vercel`), not automated on merge.

## Docs

`docs/superpowers/plans/` and `docs/superpowers/specs/` hold dated per-feature plan/design docs (one pair per feature, e.g. `2026-06-11-backend-foundation.md` + matching spec). When completing a task tracked in one of these plans, mark its checkbox `- [x]` and commit.

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
