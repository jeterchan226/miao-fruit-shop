## ADDED Requirements

### Requirement: API 層不得直接存取 repository
`app/api/` 下的任何模組 SHALL NOT import `app.repositories` 或其子模組；架構測試 MUST 在違規時失敗並列出違規檔案。

#### Scenario: 現有程式碼
- **WHEN** 執行架構測試
- **THEN** `app/api/` 下沒有任何 `app.repositories` import，測試通過

#### Scenario: 新增違規 import
- **WHEN** `app/api/routes/` 下某檔案新增 `from app.repositories import order_repo`
- **THEN** 架構測試失敗，訊息包含該檔案路徑

### Requirement: Repository 不得反向相依
`app/repositories/` 下的模組 SHALL NOT import `app.services` 或 `app.api`。

#### Scenario: repository import service
- **WHEN** 某 repository 模組 import `app.services`
- **THEN** 架構測試失敗

### Requirement: 管理員身分解析由 service 負責
系統 SHALL 由 `auth_service` 將 access token 解析為啟用中的管理員；token 無效、管理員不存在或已停用時 MUST 拋出 `AuthError`。

#### Scenario: 停用的管理員
- **WHEN** token 有效但對應管理員 `is_active=false`
- **THEN** 回應 401 `AUTH_ERROR`
