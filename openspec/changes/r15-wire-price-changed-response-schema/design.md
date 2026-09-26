## Context

錯誤回應由 `api/errors.py` 的 exception handler 產生，形狀固定為 `{detail, code}`（`PRICE_CHANGED` 另有金額欄位），但 FastAPI 預設只在文件中列出 200/201 與 422。

## Goals / Non-Goals

**Goals:** 錯誤形狀可從 OpenAPI 得知；消除死碼。

**Non-Goals:** 不產生前端型別（專案前端為 JS）；不改錯誤回應實際形狀。

## Decisions

- **以 `responses=` 參數宣告**，並集中在 `api/responses.py` 定義常用組合（如 `ADMIN_ERRORS = {401: ..., 404: ..., 409: ...}`），避免每個 route 重複。
- 409 在下單端點同時可能是一般錯誤或 `PRICE_CHANGED`；使用 `PriceChangedResponse`（`code` 欄位為字串，其他金額欄位設為 optional）作為 409 的 schema，並在 description 說明。替代方案 `oneOf` 需自訂 OpenAPI，成本過高。
- 以測試讀取 `app.openapi()` 斷言，而非快照整份文件（避免無關變更造成測試脆弱）。

## Risks / Trade-offs

- [宣告與實際回應不同步] → 測試只驗證宣告存在；實際形狀由既有 `test_errors.py` 覆蓋。
