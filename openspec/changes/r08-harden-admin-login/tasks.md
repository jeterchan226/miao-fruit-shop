## 1. 紅燈：金鑰強度

- [ ] 1.1 `tests/test_config.py`：`JWT_SECRET` 少於 32 bytes 時 `Settings()` 拋 `ValidationError`
- [ ] 1.2 確認失敗

## 2. 綠燈：金鑰強度

- [ ] 2.1 `config.py` 的 `jwt_secret` 加 `min_length=32`；更新 CI、本地 `.env.example` 與測試所需的值
- [ ] 2.2 執行 1.1 通過

## 3. 紅燈：帳號鎖定（資料庫）

- [ ] 3.1 `tests/test_auth_service.py`：連續 5 次失敗後正確密碼拋 `AccountLockedError`
- [ ] 3.2 失敗 4 次後成功登入，`failed_login_count` 歸零
- [ ] 3.3 以可注入時鐘測試：鎖定 15 分鐘後可登入且計數歸零
- [ ] 3.4 鎖定狀態跨 session：用另一個新的 session 讀取仍為鎖定
- [ ] 3.5 不存在的帳號登入不寫入任何資料；鎖定期間不呼叫 `verify_password`（以 mock 斷言）
- [ ] 3.6 成功登入且原本計數為 0 時不發出 `UPDATE`（以 SQLAlchemy event 計數斷言）
- [ ] 3.7 `tests/test_cli.py`（或既有 CLI 測試）：`unlock-admin` 清除計數與鎖定
- [ ] 3.8 確認上述測試失敗

## 4. 綠燈：帳號鎖定

- [ ] 4.1 `AdminUser` 新增 `failed_login_count`、`locked_until`；新增 migration（`server_default` 0 / null）
- [ ] 4.2 `admin_repo` 新增 `get_by_username_for_update`
- [ ] 4.3 `auth_service.authenticate` 實作 design 中的五步流程，新增 `AccountLockedError`（429 `ACCOUNT_LOCKED`）
- [ ] 4.4 `cli.py` 新增 `unlock-admin` 子指令
- [ ] 4.5 登入失敗與鎖定寫 warning log
- [ ] 4.6 執行 3.x 測試通過

## 5. 紅燈 → 綠燈：IP 節流

- [ ] 5.1 `tests/test_admin_auth_api.py`：IP 第 11 次請求回 429 `RATE_LIMITED`，確認失敗
- [ ] 5.2 新增 `core/rate_limit.py`（若 r02 已建立則沿用），登入端點套用 `10/minute`
- [ ] 5.3 測試 fixture 在每個測試前重設 limiter
- [ ] 5.4 執行 5.1 通過

## 6. 重構與驗證

- [ ] 6.1 若 r09 已完成，確認 migration 一致性測試通過
- [ ] 6.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 7. 收尾

- [ ] 7.1 確認正式環境 `jwt-secret` 長度 ≥ 32（只看長度，不輸出內容）
- [ ] 7.2 CLAUDE.md Commands 區補上 `unlock-admin`
- [ ] 7.3 以 `feat(admin-auth): 登入節流、資料庫帳號鎖定與 JWT 金鑰長度檢查` 提交
