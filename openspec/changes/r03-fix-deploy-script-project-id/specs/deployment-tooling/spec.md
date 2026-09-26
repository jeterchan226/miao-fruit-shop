## ADDED Requirements

### Requirement: 部署目標 project 以單一來源解析
部署腳本 SHALL 依序以環境變數 `PROJECT`、`terraform/terraform.tfvars` 的 `project_id` 決定 GCP project，且 MUST NOT 使用寫死的預設 project id。

#### Scenario: 未設環境變數時讀取 tfvars
- **WHEN** 未設定 `PROJECT`，且 tfvars 內容為 `project_id = "miao-fruit-shop-504712"`
- **THEN** 解析結果為 `miao-fruit-shop-504712`

#### Scenario: 環境變數優先
- **WHEN** `PROJECT=other-project`
- **THEN** 解析結果為 `other-project`

#### Scenario: 無任何來源時失敗
- **WHEN** 未設 `PROJECT`，且 tfvars 不存在或沒有 `project_id`
- **THEN** 腳本以非 0 結束並顯示錯誤，不執行任何 gcloud 部署指令
