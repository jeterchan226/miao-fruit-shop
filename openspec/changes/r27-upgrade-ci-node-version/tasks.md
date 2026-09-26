## 1. 紅燈

- [ ] 1.1 新增 `frontend/src/nodeConfig.test.js`（vitest）：讀取 `.nvmrc`、`package.json`、`../.github/workflows/ci.yml`，斷言三者一致且 ci.yml 無寫死 `node-version`
- [ ] 1.2 執行 `npm run test` 確認失敗（`.nvmrc` 不存在）

## 2. 綠燈

- [ ] 2.1 新增 `frontend/.nvmrc`（`24`）；`package.json` 加 `"engines": {"node": ">=24 <25"}`
- [ ] 2.2 `ci.yml` 改用 `node-version-file: frontend/.nvmrc`，並新增 `npm run test` 步驟
- [ ] 2.3 以 Node 24 執行 `npm install && npm run build && npm run test` 通過

## 3. 驗證

- [ ] 3.1 推到 PR 確認 CI frontend job 使用 Node 24 且通過
- [ ] 3.2 確認 Vercel 專案 Node 版本設定為 24.x

## 4. 收尾

- [ ] 4.1 以 `ci(frontend): Node 升級至 24 並以 .nvmrc 為單一來源` 提交
