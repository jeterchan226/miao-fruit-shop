# 開發進度快照

格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 系統現況

（每完成一個 ticket，用 1–3 句更新系統目前能做什麼。）

前端 Node 版本宣告於根目錄 `package.json` 的 `engines.node`（24.x），CI 前端 job 依此取得版本並以 `npm ci` 驗證 lockfile。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 31 | CI Node 版本從 20 升級 | `upgrade-ci-node-lts` | 2026-10-30 | [紀錄](tickets/31-upgrade-ci-node-lts.md) |

## 留待之後

| 項目 | 來源 ticket | 備註 |
|---|---|---|
| 確認 PR #76 的 CI log 與 Vercel build log 顯示 Node 24 | #31 | log 需登入；Vercel `rootDirectory` metadata 為 `null`，根目錄 `engines` 應生效 |
| `frontend/Dockerfile` 的 Node 版本與 `engines` 不同步 | #31 | #79 |
| Vercel `installCommand` 未依 lockfile 安裝 | #31 | #80 |
| 移除疑似舊檔 `frontend/vercel.json` | #31 | #81 |

## 下一步建議

- 登入後看 PR #76 的 CI log 與 Vercel build log，確認 Node 24（#31）。
