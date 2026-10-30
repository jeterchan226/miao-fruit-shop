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
- [ ] Node 版本單一宣告 — Vercel build 與 CI 版本一致：repo 端已宣告，PR #76 的 Vercel preview 部署 Ready，bot comment metadata 的 `rootDirectory` 為 `null`（repo 根目錄），但 build log 需登入 Vercel，尚未確認版本。
- [x] CI 依 lockfile 驗證前端 — 安裝、測試與 build 全數通過：PR 的 CI frontend job；本機 Node 24.22 / npm 11.19 `npm ci`、106 tests、build 通過。
- [x] CI 依 lockfile 驗證前端 — lockfile 不同步時失敗：乾淨副本把 `react` 改成 `^17.0.0` 不更新 lockfile，`npm ci` exit 1，`EUSAGE`，`Invalid: lock file's react@18.3.1 does not satisfy react@17.0.2`。

## 留待之後
- 登入確認 PR #76 的 CI log 與 Vercel build log 顯示 Node 24；不是 24 時依 design.md Risks 處理。
- `frontend/Dockerfile` 的 Node 版本與 `engines` 不同步：#79。
- Vercel `installCommand` 未依 lockfile 安裝：#80。
- 移除疑似舊檔 `frontend/vercel.json`：#81。

## 下一步
- 

## Review
- 
