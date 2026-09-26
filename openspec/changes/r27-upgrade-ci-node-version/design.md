## Context

目前 `ci.yml` 寫死 `node-version: "20"`；本機使用 nvm（v22.19.0）；Vercel 預設 Node 24。

## Goals / Non-Goals

**Goals:** 三個環境版本一致並有單一來源。

**Non-Goals:** 不升級前端相依套件（除非 Node 24 下建置失敗）。

## Decisions

- **選 Node 24**：與 Vercel 預設一致，且為目前 LTS。
- `setup-node` 使用 `node-version-file: frontend/.nvmrc`。
- 「測試」為一個小型 Node 腳本 `frontend/scripts/check-node-config.mjs`（或 vitest 測試），檢查 `.nvmrc`、`engines`、`ci.yml` 三者一致，於 CI 執行。

## Risks / Trade-offs

- [Vite 8 或其他套件在 Node 24 下有問題] → 先在本機以 Node 24 執行 `npm ci && npm run build && npm run test` 驗證。
