## ADDED Requirements

### Requirement: 前端 Node 版本單一來源
CI 的前端建置 SHALL 讀取 `frontend/.nvmrc` 決定 Node 版本，且該版本 MUST 為仍受支援的 LTS 版本並與 `package.json` 的 `engines.node` 相容。

#### Scenario: CI 使用的版本
- **WHEN** CI frontend job 執行
- **THEN** `node --version` 輸出的主版本與 `frontend/.nvmrc` 相同

#### Scenario: 設定一致性檢查
- **WHEN** 執行設定檢查腳本
- **THEN** `.nvmrc` 主版本符合 `engines.node` 範圍，且 `ci.yml` 沒有寫死 `node-version`
