## ADDED Requirements

### Requirement: 下單錯誤回應寫入 OpenAPI
系統 SHALL 在 OpenAPI 文件中為 `POST /api/orders` 宣告 404 與 409 回應，且 409 的 schema MUST 包含 `PRICE_CHANGED` 回應的金額欄位。

#### Scenario: 讀取 OpenAPI 文件
- **WHEN** 取得 `/openapi.json`
- **THEN** `paths./api/orders.post.responses` 含 `404` 與 `409`，且 409 引用的 schema 含 `subtotal`、`shipping_fee`、`total`

### Requirement: 共用錯誤回應 schema
系統 SHALL 以單一 `ErrorResponse` schema（`detail: string`、`code: string`）描述所有 `AppError` 類錯誤回應。

#### Scenario: 後台端點宣告錯誤
- **WHEN** 取得 `/openapi.json`
- **THEN** `PATCH /api/admin/orders/{order_no}/status` 的 `401`、`404`、`409` 回應引用 `ErrorResponse`
