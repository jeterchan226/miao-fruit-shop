## Why

審查 #3：`backend/deploy.sh` 的 `PROJECT` 預設值仍是舊的 `miao-fruit-shop-499505`，但 2026-08 起正式環境已遷到 `miao-fruit-shop-504712`（見 `terraform/terraform.tfvars`）。沒有設定 `PROJECT` 直接執行時，會部署到舊 project 或因權限失敗。

## What Changes

- `deploy.sh` 不再寫死 project id，改從 `terraform/terraform.tfvars` 的 `project_id` 讀取；仍可用環境變數 `PROJECT` 覆寫。
- 讀不到 project id 時直接失敗，不再使用任何預設值。
- 部署前確認畫面顯示 project id 的來源（env 或 tfvars）。
- 新增 shell 測試（bats）涵蓋 project id 解析。

## Capabilities

### New Capabilities
- `deployment-tooling`: 後端部署腳本的目標解析與安全檢查。

### Modified Capabilities
（無）

## Impact

- `backend/deploy.sh`
- 新增 `backend/scripts/resolve_project.sh`（可被測試的函式）與 `backend/tests/shell/deploy_project.bats`
- CI 新增 bats 步驟（可選，見 tasks）
