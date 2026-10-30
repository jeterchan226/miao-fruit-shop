# 開發進度快照

格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 系統現況

#67 為純重構，未改變系統能力。

訂單品項保存包裝類型快照：既有訂單品項的層數與雙數檢查不受規格改動或刪除影響，後台試算讀同一份快照。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 46 | 訂單品項快照加入「是否兩粒裝」 | `add-order-item-pack-snapshot` | 2026-10-30 | [紀錄](tickets/46-add-order-item-pack-snapshot.md) |
| 67 | 前端訂單來源、付款方式字串改用常數模組 | `extract-frontend-order-constants` | 2026-10-30 | [紀錄](tickets/67-extract-frontend-order-constants.md) |

## 留待之後

| 項目 | 來源 ticket | 備註 |
|---|---|---|
| 錯誤訊息改用快照名稱與正確用語 | #46 | 追蹤於 #83，可併入 #45 |
| GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改的落差 | #46 | 追蹤於 #84 |
| ADR 0003／0004 未提包裝類型快照 | #46 | 追蹤於 #85 |
| 公開下單回應不含後台欄位缺明確自動測試 | #67 | #82；`test_create_order_201` 只斷言 `stock_qty` |

## 下一步建議

- 部署 #46：先跑 migration，立刻部署後端，再部署前端。
- 處理「留待之後」的 #82。
