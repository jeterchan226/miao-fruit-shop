# api-platform Specification

## Purpose

描述所有 API 共通的對外行為：健康檢查端點、業務錯誤的回應格式，以及跨來源請求的放行範圍。各領域的具體錯誤碼定義在各自的 capability。

## Requirements

### Requirement: 健康檢查

系統 SHALL 在 `GET /health` 不需登入即回傳 200 與 `{"status": "ok"}`。

#### Scenario: 服務運作中

- **WHEN** 呼叫健康檢查
- **THEN** 系統回傳 200 與 `status` 為 `ok`

### Requirement: 業務錯誤回應格式

系統 SHALL 以 JSON 回傳業務錯誤，含人類可讀的 `detail` 與機器可讀的 `code`，並使用對應的 HTTP 狀態碼：找不到 404、未授權 401、業務衝突 409。

#### Scenario: 找不到資源

- **WHEN** 請求的資源不存在
- **THEN** 系統回傳 404，`code` 為 `NOT_FOUND`

#### Scenario: 認證失敗

- **WHEN** 業務層判定認證失敗
- **THEN** 系統回傳 401，`code` 為 `AUTH_ERROR`

#### Scenario: 庫存不足

- **WHEN** 業務層判定庫存不足
- **THEN** 系統回傳 409，`code` 為 `INSUFFICIENT_STOCK`

### Requirement: 金額變動錯誤附帶金額明細

`PRICE_CHANGED` 錯誤回應 SHALL 在 `detail`、`code` 之外另含 `subtotal`、`shipping_fee`、`cod_fee`、`total`。

#### Scenario: 金額不符

- **WHEN** 系統回傳 `PRICE_CHANGED`
- **THEN** 回應體含最新的金額明細

### Requirement: 跨來源請求放行範圍

系統 SHALL 只放行設定白名單內的來源，以及本團隊 Vercel 專案的部署與分支網址；白名單比對前 SHALL 去除設定值的結尾斜線，其他來源 MUST NOT 取得跨來源授權。

#### Scenario: 白名單來源

- **WHEN** 請求來源在設定白名單內
- **THEN** 回應帶該來源的 `access-control-allow-origin`

#### Scenario: 本團隊的 Vercel 部署

- **WHEN** 請求來源為本團隊 Vercel 專案的 preview、分支或部署別名網址
- **THEN** 回應帶該來源的 `access-control-allow-origin`

#### Scenario: 其他 Vercel 專案

- **WHEN** 請求來源為其他 Vercel 專案，或以相同專案名前綴但無團隊後綴的網址
- **THEN** 回應不帶 `access-control-allow-origin`

#### Scenario: 偽造的網域後綴

- **WHEN** 請求來源在本團隊網址後再接其他網域
- **THEN** 回應不帶 `access-control-allow-origin`

#### Scenario: 未知來源

- **WHEN** 請求來源不在放行範圍內
- **THEN** 回應不帶 `access-control-allow-origin`
