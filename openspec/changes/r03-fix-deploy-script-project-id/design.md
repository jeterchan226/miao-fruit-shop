## Context

Terraform 是 GCP 資源的唯一來源，`terraform.tfvars` 已含正確 `project_id`。deploy.sh 另外寫死一份，換 project 時沒人記得同步。

## Goals / Non-Goals

**Goals:** project id 只有一個來源；解析失敗 fail-fast。

**Non-Goals:** 不把部署改成 Terraform 或 CI 自動化（已決定 CD 維持手動）。

## Decisions

- **讀 tfvars，而非 `terraform output`**：`terraform output` 需先 `init` 並存取 remote state，較慢且需要權限；tfvars 為純文字、已在 repo（若將來移出 repo，可改讀 `gcloud config get-value project` 作為第二順位）。
- **抽出 `resolve_project` 函式到獨立檔案**，讓 bats 可以 source 測試，不必執行整個部署腳本。
- 解析用 `sed -n 's/^project_id *= *"\(.*\)"/\1/p'`，相容 macOS BSD sed。

## Risks / Trade-offs

- [tfvars 被加入 .gitignore 後讀不到] → 會 fail-fast 並提示設定 `PROJECT`，不會誤部署。
- [團隊需安裝 bats] → `brew install bats-core`；CI 用 apt 安裝。
