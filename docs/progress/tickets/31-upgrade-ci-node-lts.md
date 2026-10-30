# #31 CI Node 版本從 20 升級

- 狀態：完成
- OpenSpec change：`upgrade-ci-node-lts`（archive 後：`openspec/changes/archive/2026-10-30-upgrade-ci-node-lts/`）
- Branch：`claude/nifty-montalcini-1713f6`
- 最後更新：2026-10-30

## 做了什麼
- 根目錄 `package.json` 宣告 `engines.node: "24.x"`，為 Node 版本單一來源。
- CI 前端 job 由 `node-version-file: package.json` 取得版本，改在 `frontend/` 內跑 `npm ci`、`npm test`、`npm run build`。
- `README.md` 的 Node.js 版本需求改為 24。

## 決定與偏離
- task 2.1 未重現：`npm ci --prefix frontend` 在 worktree 與 `git archive` 乾淨副本皆 exit 0，與 design.md 原記錄不符。`working-directory` 作法不變，理由改為與 lockfile 所在目錄一致；design.md 已更正。
- `frontend/Dockerfile` 的 `node:22-alpine` 依 design.md Non-Goals 不動，是 repo 內第二個 Node 版本字串，但不屬於 CI / Vercel 路徑。

## 驗收結果
- [ ] Node 版本單一宣告 — CI 使用宣告的 LTS 版本：PR #76 的 frontend job 綠燈，`actions/setup-node` 步驟成功，但 log 需登入 GitHub 才能看，尚未親眼確認 `v24`。
- [ ] Node 版本單一宣告 — Vercel build 與 CI 版本一致：repo 端已宣告，PR #76 的 Vercel preview 部署 Ready，但 build log 需登入 Vercel，尚未確認版本。
- [x] CI 依 lockfile 驗證前端 — 安裝、測試與 build 全數通過：PR 的 CI frontend job；本機 Node 24.22 / npm 11.19 `npm ci`、106 tests、build 通過。
- [x] CI 依 lockfile 驗證前端 — lockfile 不同步時失敗：乾淨副本把 `react` 改成 `^17.0.0` 不更新 lockfile，`npm ci` exit 1，`EUSAGE`，`Invalid: lock file's react@18.3.1 does not satisfy react@17.0.2`。

## 留待之後
- 確認 Vercel 專案 Root Directory 是 repo 根目錄：repo 同時有 `vercel.json` 與 `frontend/vercel.json`，若 Root Directory 是 `frontend`，根目錄 `engines` 不生效。看第一次部署的 build log，不是 24 時依 design.md Risks 處理。
- `frontend/vercel.json` 疑似舊檔（最後改動早於根目錄 `vercel.json`），確認 Root Directory 後可刪。
- Vercel `installCommand` 仍是 `npm install --prefix frontend`，正式 build 不經 lockfile 驗證。

## 下一步
- 

## Review
- 
