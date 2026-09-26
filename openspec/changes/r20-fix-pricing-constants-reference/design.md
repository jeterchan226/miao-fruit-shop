## Context

`compute_layers`、`compute_shipping` 在前後端各實作一次，公式相同但沒有共同測試。CI 的 backend job 會 checkout 整個 repo，因此 pytest 可以讀取 `frontend/src/pricing.js`。

## Goals / Non-Goals

**Goals:** 任一邊單獨修改都會讓 CI 失敗。

**Non-Goals:** 不改為前端從 API 取得運費規則（會增加一次請求與 iPadOS 15 首載時間）。

## Decisions

- **常數比對用正規表示式解析 `pricing.js`**：只抓 `export const FREE_SHIPPING = <int>;` 與 `SHIPPING_BY_LAYER = { ... }`，不必在 Python 執行 JS。
- **案例放 repo 根目錄 `shared/`**，前後端測試都能以相對路徑讀取；vitest 以 `import cases from '../../shared/pricing-cases.json'`（Vite 支援 JSON import）。
- 案例使用前端資料形狀（`{price, count, isTwoPack}`），pytest 端轉成後端 tuple。

## Risks / Trade-offs

- [`pricing.js` 格式改變導致正規表示式失效] → 解析不到時測試明確失敗並提示更新解析器，而非靜默通過。
