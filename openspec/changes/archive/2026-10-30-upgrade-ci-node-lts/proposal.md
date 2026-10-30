Ticket: #31

## Why

CI 前端 job 仍釘 Node 20，該版本已於 2026-04 EOL；repo 內也沒有任何地方宣告 Node 版本，Vercel build 用的版本只存在專案設定裡，無法確認與 CI 一致。CI 驗過的環境若與正式 build 不同，綠燈就不能代表正式部署可行。

## What Changes

- 前端的 Node 版本升到 24 LTS，並在 repo 內宣告為單一來源。
- CI 前端 job 與 Vercel build 都依這個宣告取得 Node 版本，不再各自設定。
- CI 前端 job 改為依 lockfile 安裝相依（`npm ci`），lockfile 與 package.json 不同步時直接失敗。
- 開發文件的 Node 版本需求同步更新。

## User Stories

1. 身為維護者，我想要 CI 使用仍受支援的 Node LTS，以便不在已 EOL 的版本上驗證程式。
2. 身為維護者，我想要 CI 與 Vercel 使用同一個 Node 版本宣告，以便 CI 綠燈能代表正式 build 的環境。
3. 身為維護者，我想要 CI 依 lockfile 安裝相依，以便驗證的相依版本就是 lockfile 鎖定的版本。

## Capabilities

### New Capabilities

- `frontend-toolchain`: 前端的 Node 版本宣告，以及 CI 對前端的安裝、測試、build 驗證。

### Modified Capabilities

（無）

## Impact

- CI 前端 job、repo 根目錄的套件宣告、開發文件。
- Vercel build 的 Node 版本改由 repo 決定，下次部署起生效；顧客與管理員可見的行為不變。
- 後端、API、資料庫不受影響。
