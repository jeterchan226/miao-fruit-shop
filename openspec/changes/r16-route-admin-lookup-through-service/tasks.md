## 1. 紅燈

- [ ] 1.1 新增 `tests/test_architecture.py`：掃描 `app/api/**/*.py` 禁止 `app.repositories`；掃描 `app/repositories/**/*.py` 禁止 `app.services`、`app.api`
- [ ] 1.2 `tests/test_auth_service.py` 新增 `get_active_admin` 測試：有效、token 無效、管理員不存在、已停用
- [ ] 1.3 確認 1.1 因 `deps.py` 失敗、1.2 因函式不存在失敗

## 2. 綠燈

- [ ] 2.1 實作 `auth_service.get_active_admin(session, token)`
- [ ] 2.2 `deps.get_current_admin` 改呼叫 service，移除 `admin_repo`、`decode_access_token` import
- [ ] 2.3 執行 1.x 測試通過

## 3. 重構與驗證

- [ ] 3.1 調整 `tests/test_deps.py`
- [ ] 3.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 4. 收尾

- [ ] 4.1 以 `refactor(auth): 管理員身分解析移入 service 並加入分層架構測試` 提交
