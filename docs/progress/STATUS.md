# 開發進度快照

格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 系統現況

#67 為純重構，未改變系統能力。

前端 Node 版本宣告於根目錄 `package.json` 的 `engines.node`（24.x），CI 前端 job 依此取得版本並以 `npm ci` 驗證 lockfile。
訂單品項保存包裝類型快照：既有訂單品項的層數與雙數檢查不受規格改動或刪除影響，後台試算讀同一份快照。
既有訂單品項的雙數限制與庫存不足訊息以快照名稱稱呼；後台 `PRICE_CHANGED` 提示涵蓋規格價格與包裝類型。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 31 | CI Node 版本從 20 升級 | `upgrade-ci-node-lts` | 2026-10-30 | [紀錄](tickets/31-upgrade-ci-node-lts.md) |
| 46 | 訂單品項快照加入「是否兩粒裝」 | `add-order-item-pack-snapshot` | 2026-10-30 | [紀錄](tickets/46-add-order-item-pack-snapshot.md) |
| 67 | 前端訂單來源、付款方式字串改用常數模組 | `extract-frontend-order-constants` | 2026-10-30 | [紀錄](tickets/67-extract-frontend-order-constants.md) |
| 83 | 訂單品項錯誤訊息改用快照名稱與正確用語 | `correct-order-item-error-messages` | 2026-10-31 | [紀錄](tickets/83-correct-order-item-error-messages.md) |

## 留待之後

| 項目 | 來源 ticket | 備註 |
|---|---|---|
| 確認 PR #76 的 Vercel build log 顯示 Node 24 | #31 | log 需登入；Vercel `rootDirectory` metadata 為 `null`，根目錄 `engines` 應生效 |
| `frontend/Dockerfile` 的 Node 版本與 `engines` 不同步 | #31 | #79 |
| Vercel `installCommand` 未依 lockfile 安裝 | #31 | #80 |
| 移除疑似舊檔 `frontend/vercel.json` | #31 | #81 |
| GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改的落差 | #46 | 追蹤於 #84 |
| GLOSSARY「規格名稱建立後不變」與規格更新 API 可改 `label` 的落差 | #83 | 追蹤於 #98 |
| 雙數限制訊息「2 粒裝」改「兩粒裝」 | #83 | 追蹤於 #45；後合併者須保留快照名稱 |
| ADR 0003／0004 未提包裝類型快照 | #46 | 追蹤於 #85 |
| 公開下單回應不含後台欄位缺明確自動測試 | #67 | #82；`test_create_order_201` 只斷言 `stock_qty` |

## 下一步建議

- 部署 #46：先跑 migration，立刻部署後端，再部署前端。
- 處理「留待之後」的 #82。
- 登入後看 PR #76 的 Vercel build log，確認 Node 24（#31）。
