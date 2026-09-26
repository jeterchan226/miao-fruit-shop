## ADDED Requirements

### Requirement: 登入嘗試節流
系統 SHALL 限制同一來源 IP 每分鐘最多 10 次登入請求，超過時 MUST 回應 429 `RATE_LIMITED`。

#### Scenario: IP 超過每分鐘上限
- **WHEN** 同一 IP 在一分鐘內送出第 11 次登入請求
- **THEN** 回應 429 `RATE_LIMITED`

### Requirement: 帳號連續失敗鎖定
系統 SHALL 將帳號的連續登入失敗次數與鎖定期限存於資料庫；同一帳號連續失敗 5 次後 MUST 在 15 分鐘內拒絕該帳號的登入（即使密碼正確），且鎖定狀態 MUST 在所有應用程式 instance 間一致。

#### Scenario: 帳號連續失敗後鎖定
- **WHEN** 帳號 `admin` 連續 5 次密碼錯誤後，以正確密碼登入
- **THEN** 回應 429 `ACCOUNT_LOCKED`，不簽發 token

#### Scenario: 鎖定狀態跨 session 生效
- **WHEN** 帳號在一個資料庫 session 中被鎖定，另一個新的 session 以正確密碼登入
- **THEN** 回應 429 `ACCOUNT_LOCKED`

#### Scenario: 鎖定到期自動解除
- **WHEN** 帳號鎖定超過 15 分鐘後以正確密碼登入
- **THEN** 登入成功，失敗次數歸零

#### Scenario: 成功登入重置失敗計數
- **WHEN** 帳號連續失敗 4 次後以正確密碼登入成功
- **THEN** 失敗次數歸零

#### Scenario: 不存在的帳號
- **WHEN** 以不存在的帳號登入
- **THEN** 回應 401 `AUTH_ERROR`，不寫入任何資料

#### Scenario: 手動解鎖
- **WHEN** 管理者執行 `python -m app.cli unlock-admin --username admin`
- **THEN** 該帳號失敗次數歸零、鎖定期限清除

### Requirement: JWT 金鑰強度
系統 SHALL 在啟動時驗證 `JWT_SECRET` 長度至少 32 bytes，不足時 MUST 拒絕啟動。

#### Scenario: 金鑰過短
- **WHEN** `JWT_SECRET="short"`
- **THEN** 建立 `Settings` 時拋出驗證錯誤
