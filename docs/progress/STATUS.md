# 開發進度快照

格式與規則見 [README.md](README.md)。自 2026-10-30 起記錄；更早的 ticket 見 git log 與 `docs/superpowers/`。

## 系統現況

前端的訂單來源與付款方式集中於 `frontend/src/constants.js`；前後端仍各有一份定義，須手動保持一致。

## 已完成

| # | 標題 | OpenSpec change | 完成日 | 紀錄 |
|---|---|---|---|---|
| 67 | 前端訂單來源、付款方式字串改用常數模組 | `extract-frontend-order-constants` | 2026-10-30 | [紀錄](tickets/67-extract-frontend-order-constants.md) |

## 留待之後

| 項目 | 來源 ticket | 備註 |
|---|---|---|
| `PAYMENT_METHOD_LABELS` 物件 key 仍手寫 `transfer` | #67 | 可改 `[PAYMENT_METHOD_TRANSFER]` |
| 公開下單回應不含後台欄位缺明確自動測試 | #67 | `test_create_order_201` 只斷言 `stock_qty` |

## 下一步建議

- 處理「留待之後」兩項小修。
