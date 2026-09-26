## 1. 紅燈

- [ ] 1.1 新增 `backend/tests/shell/deploy_project.bats`：涵蓋「讀 tfvars」「PROJECT 覆寫」「無來源時失敗」三個情境（使用暫存 tfvars fixture）
- [ ] 1.2 執行 `bats backend/tests/shell` 確認失敗（函式尚不存在）

## 2. 綠燈

- [ ] 2.1 新增 `backend/scripts/resolve_project.sh`，實作 `resolve_project <tfvars_path>`
- [ ] 2.2 `deploy.sh` source 該檔，移除寫死的 `miao-fruit-shop-499505`，確認畫面顯示來源
- [ ] 2.3 執行 bats 通過

## 3. 重構與驗證

- [ ] 3.1 `bash -n backend/deploy.sh` 語法檢查；可用 `shellcheck` 則一併執行
- [ ] 3.2 以 `./deploy.sh` 走到確認步驟後回答 N，確認顯示 `miao-fruit-shop-504712`
- [ ] 3.3 （可選）CI 新增 bats job

## 4. 收尾

- [ ] 4.1 以 `fix(deploy): 部署 project 改由 terraform.tfvars 解析，移除過期預設值` 提交
