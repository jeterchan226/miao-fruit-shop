## 1. Node 版本單一宣告

- [ ] 1.1 Failing check：在根目錄跑 `node -p "require('./package.json').engines?.node"`，確認輸出 `undefined`
- [ ] 1.2 根目錄 `package.json` 加 `"engines": { "node": "24.x" }`，1.1 的檢查輸出 `24.x`
- [ ] 1.3 `.github/workflows/ci.yml` 前端 job 的 `actions/setup-node` 改用 `node-version-file: package.json`，移除 `node-version`
- [ ] 1.4 `README.md` 的 Node.js 版本需求改為 24

## 2. CI 依 lockfile 驗證前端

- [ ] 2.1 Failing check：在 Node 24 / npm 11 下跑 `npm ci --prefix frontend`，確認 `EUSAGE` 失敗，證明不能直接替換現有指令
- [ ] 2.2 CI 前端 job 加 `defaults.run.working-directory: frontend`，指令改為 `npm ci`、`npm test`、`npm run build`
- [ ] 2.3 在暫時改動 `frontend/package.json` 版本範圍、不更新 lockfile 的情況下跑 `npm ci`，確認失敗後還原

## 3. Verification

- [ ] 3.1 本機在 `frontend/` 內 `npm ci`、`npm test`、`npm run build` 通過
- [ ] 3.2 後端未變更，不跑 ruff / mypy / pytest，由 PR 的 CI backend job 確認
- [ ] 3.3 PR 的 CI 前端 job 通過，log 顯示 Node v24
- [ ] 3.4 檢查 Vercel build log 的 Node 版本為 24，結果（或尚待部署的狀態）記入 ticket 進度紀錄
