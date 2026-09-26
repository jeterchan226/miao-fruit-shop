## ADDED Requirements

### Requirement: 跨來源請求不攜帶憑證
系統 SHALL NOT 在 CORS 回應中送出 `Access-Control-Allow-Credentials: true`。

#### Scenario: 白名單來源的預檢請求
- **WHEN** 允許的來源對 `/api/products` 發出 OPTIONS 預檢
- **THEN** 回應包含 `Access-Control-Allow-Origin` 為該來源，且不包含 `Access-Control-Allow-Credentials: true`

### Requirement: 允許的方法與標頭最小化
系統 SHALL 只允許 `GET`、`POST`、`PATCH`、`DELETE` 方法與 `Authorization`、`Content-Type` 請求標頭的跨來源請求。

#### Scenario: 帶 Authorization 的後台預檢
- **WHEN** 允許的來源以 `Access-Control-Request-Method: PATCH`、`Access-Control-Request-Headers: authorization,content-type` 發出預檢
- **THEN** 預檢成功（200）

#### Scenario: 不允許的方法
- **WHEN** 允許的來源以 `Access-Control-Request-Method: PUT` 發出預檢
- **THEN** 預檢失敗（400）
