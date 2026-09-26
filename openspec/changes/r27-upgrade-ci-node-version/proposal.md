## Why

審查 #27：CI 的 frontend job 使用 Node 20，Node 20 將於 2026-10-01 結束支援，Vercel 也將其列為 deprecated（目前預設為 Node 24）。CI 與正式建置環境的 Node 版本不同，可能出現「CI 綠燈、Vercel 建置失敗」或相反的情況。

## What Changes

- CI frontend job 改用 Node 24（與 Vercel 預設一致）。
- 新增 `frontend/.nvmrc` 與 `package.json` 的 `engines.node`，讓本地、CI、Vercel 使用同一版本來源。
- CI 讀取 `.nvmrc`（`node-version-file`），不再寫死版本。

## Capabilities

### New Capabilities
- `ci-pipeline`: 前端建置的 Node 版本一致性。

### Modified Capabilities
（無）

## Impact

- `.github/workflows/ci.yml`、新增 `frontend/.nvmrc`、`frontend/package.json`
- Vercel 專案設定的 Node 版本需確認為 24.x
