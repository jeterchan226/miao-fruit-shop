## ADDED Requirements

### Requirement: mypy strict 為必要檢查
CI SHALL 對 `backend/app` 執行 `mypy`（strict 設定），任何錯誤 MUST 使 CI 失敗。

#### Scenario: 新增未標註型別的函式
- **WHEN** PR 新增一個沒有回傳型別標註的函式
- **THEN** CI 的 backend job 失敗

#### Scenario: 目前程式碼
- **WHEN** 在本 change 完成後的 master 執行 `uv run mypy app`
- **THEN** 輸出 `Success: no issues found`
