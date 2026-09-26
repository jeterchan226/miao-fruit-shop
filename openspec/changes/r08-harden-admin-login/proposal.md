## Why

審查 #8：`POST /api/admin/auth/login` 沒有任何節流或失敗鎖定，可被無限次暴力嘗試密碼；`JWT_SECRET` 也沒有長度檢查，設定成短字串時 HS256 簽章可被離線破解，攻擊者即可偽造管理員 token。

## What Changes

- 登入端點加上 IP 速率限制：同一 IP 每分鐘最多 10 次，超過回 429。
- 帳號鎖定：同一帳號連續失敗 5 次後鎖定 15 分鐘，期間回 429。鎖定狀態存在資料庫（`admin_users.failed_login_count`、`admin_users.locked_until`），Cloud Run 多個 instance 之間一致。
- 新增 CLI `python -m app.cli unlock-admin --username <name>` 手動解鎖。
- `Settings` 驗證 `jwt_secret` 長度至少 32 bytes，不足時應用程式啟動失敗。
- 登入失敗與鎖定事件寫入 log（不含密碼）。

## Capabilities

### New Capabilities
- `admin-auth`: 後台登入的暴力破解防護與金鑰強度。

### Modified Capabilities
（無）

## Impact

- `backend/app/models/admin_user.py`、新 migration（`admin_users` 新增兩個欄位）
- `backend/app/repositories/admin_repo.py`、`backend/app/services/auth_service.py`、`backend/app/api/routes/admin_auth.py`、`backend/app/cli.py`、`backend/app/core/config.py`
- 新相依 `slowapi`（與 r02 共用）
- CI 的 `JWT_SECRET` GitHub Secret、正式環境 Secret Manager 需確認長度 ≥ 32（Terraform 產生的值已符合）
