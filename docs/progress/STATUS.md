# 開發進度快照

由 `scripts/generate_status.py` 自動產生，勿手改；格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 部署待辦

- #46：先跑 migration，立刻部署後端，再部署前端。

## 系統現況

**#67**：純重構，未改變系統能力。

**#46**：訂單品項保存包裝類型快照：既有訂單品項的層數與雙數檢查不受規格改動或刪除影響，後台試算讀同一份快照。

**#31**：前端 Node 版本宣告於根目錄 `package.json` 的 `engines.node`（24.x），CI 前端 job 依此取得版本並以 `npm ci` 驗證 lockfile。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 31 | CI Node 版本從 20 升級 | `upgrade-ci-node-lts` | 2026-10-30 | [紀錄](tickets/31-upgrade-ci-node-lts.md) |
| 46 | 訂單品項快照加入「是否兩粒裝」 | `add-order-item-pack-snapshot` | 2026-10-30 | [紀錄](tickets/46-add-order-item-pack-snapshot.md) |
| 67 | 前端訂單來源、付款方式字串改用常數模組 | `extract-frontend-order-constants` | 2026-10-30 | [紀錄](tickets/67-extract-frontend-order-constants.md) |
| 87 | 合併到 dev 後由 GitHub Action 自動產生 docs/progress/STATUS.md | `auto-generate-progress-status` | 2026-10-30 | [紀錄](tickets/87-auto-generate-progress-status.md) |

## 留待之後

| 項目 | 來源 ticket | 追蹤 issue |
|---|---|---|
| 登入確認 PR #76 的 CI log 與 Vercel build log 顯示 Node 24；不是 24 時依 design.md Risks 處理。Vercel `rootDirectory` metadata 為 `null`，根目錄 `engines` 應生效。 | #31 | — |
| `frontend/Dockerfile` 的 Node 版本與 `engines` 不同步 | #31 | #79 |
| Vercel `installCommand` 未依 lockfile 安裝 | #31 | #80 |
| 移除疑似舊檔 `frontend/vercel.json` | #31 | #81 |
| 錯誤訊息改用快照名稱與正確用語（可併入 #45） | #46 | #83 |
| GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改的落差 | #46 | #84 |
| ADR 0003／0004 未提包裝類型快照 | #46 | #85 |
| 公開下單回應不含後台欄位缺明確的自動測試（`test_create_order_201` 只斷言 `stock_qty`） | #67 | #82 |
| 合併後確認第一次 Action run 成功、bot commit 後無新 run，勾選 #87 剩餘三條驗收並刪除本項（task 8.6）。 | #87 | — |
| bot push 沒有 rebase 或重試：checkout 到 push 之間有人直接 push 到 `dev` 時 job 失敗，下一次合併補回。 | #87 | — |
| `Closes` 指向不存在的 issue 時 close-issues 失敗，generate-status 被跳過，下一次合併補回。 | #87 | — |
| `scripts/` 不在 ruff、mypy 範圍內。 | #87 | — |
| 系統現況的純重構內容佔三格之一，例如 #67。 | #87 | — |
| 在途舊流程 PR（#29、#43、#60 的 PR）內容只在 `STATUS.md` 的部分要搬進各自紀錄，含 #29 的部署順序，否則快照漏列。 | #87 | — |
| 行尾寫成 `追蹤於 #NN。` 不算追蹤 issue，不會報錯，項目永久列出（#43 紀錄目前如此）。 | #87 | — |
