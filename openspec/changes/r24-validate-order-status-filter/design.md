## Context

FastAPI 對 `Enum` 型別的 query 參數會自動驗證並產生 OpenAPI enum。

## Goals / Non-Goals

**Goals:** 錯誤輸入明確失敗。

**Non-Goals:** 不支援多狀態同時篩選。

## Decisions

- 直接使用 `OrderStatus | None`；FastAPI 會回 422 並在 OpenAPI 列出可用值。
- 前端 `AdminApp.jsx` 的狀態 tab 值與列舉一致，經 grep 確認後不需修改。

## Risks / Trade-offs

- [前端某處傳了非列舉值（如 `all`）] → 實作前 grep 前端 `listOrders` 呼叫處確認；若有，前端改為不帶參數。
