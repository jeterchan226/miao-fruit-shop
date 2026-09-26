## Why

審查 #16：CLAUDE.md 規定 `api/` 層不得直接 import `repositories`，但 `app/api/deps.py` 的 `get_current_admin` 直接呼叫 `admin_repo.get_by_id`。目前沒有任何自動化檢查分層規則，違規只能靠 code review 發現。

## What Changes

- 新增 `auth_service.get_active_admin(session, token)`，負責解 token、查管理員、檢查 `is_active`；`deps.get_current_admin` 只呼叫 service。
- 新增架構測試：以 AST 掃描 `app/api/**`，禁止 import `app.repositories`；並禁止 `app/repositories/**` import `app.services` 或 `app.api`（防止反向相依）。

## Capabilities

### New Capabilities
- `backend-architecture`: 後端分層相依規則的自動化檢查。

### Modified Capabilities
（無）

## Impact

- `backend/app/api/deps.py`、`backend/app/services/auth_service.py`
- 新增 `backend/tests/test_architecture.py`
- `backend/tests/test_deps.py` 需依新介面調整
