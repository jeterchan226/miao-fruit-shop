# 妙媽媽果園 — Phase 2:後台驗證(Admin Auth)設計

- 日期:2026-06-11
- 狀態:待審核
- 上層 spec:`docs/superpowers/specs/2026-06-11-backend-architecture-design.md`(第 4、5、6 節)
- 前置:Phase 1 地基已完成(config、async DB、errors、測試框架、Alembic、Docker)

---

## 1. 目標與範圍

在 Phase 1 地基上,填入**後台管理員驗證骨架**,讓後續 Phase 3/4 的後台端點能用 JWT 保護。

### 本階段範圍(v1 Phase 2)
- `admin_users` ORM model + **第一個 Alembic 遷移**(autogenerate)。
- `core/security.py`:argon2 密碼雜湊 + JWT 簽發/驗證。
- `repositories/admin_repo.py`:admin_users 的資料存取。
- `services/auth_service.py`:驗證帳密、簽發 token。
- `api/deps.py`:`oauth2_scheme` 與 `get_current_admin` 依賴。
- `api/routes/admin_auth.py`:`POST /api/admin/auth/login`、`GET /api/admin/auth/me`,掛載到 app。
- `schemas/admin.py`:`Token`、`AdminRead`。
- `cli.py`:`create-admin` 指令(bootstrap 第一個管理員)。
- **小重構(分層修正)**:把領域例外**類別**從 `app/api/errors.py` 移到 `app/core/exceptions.py`,讓 Business/Data access 層能 import 例外而不依賴 Presentation 層;`app/api/errors.py` 只保留 `register_exception_handlers`(從 `core/exceptions` import 類別)。
- 對應測試(TDD)。

### 不在本階段(明確排除)
- 商品/訂單的後台端點(Phase 3/4)。
- Refresh token、登入速率限制、管理員角色權限(列未來)。
- CLI 的列表/停用/改密碼(只做 `create-admin`)。
- 顧客端登入(另案 Phase 2' LINE Login)。

### 已確認決策
1. **Bootstrap = CLI 指令**:`uv run python -m app.cli create-admin --username <name>`,密碼以 `getpass` 互動輸入(不走 `--password` 明碼參數、不進 shell history)。
2. **帳號已存在 → 報錯中止**(不覆蓋密碼)。
3. **登入格式 = OAuth2PasswordRequestForm**(form-encoded;`python-multipart` 已是相依;相容 Swagger Authorize)。
4. JWT:HS256、`sub = admin_id`、含 `exp`/`iat`,效期 `JWT_EXPIRE_MINUTES`(預設 480 分=8 小時),secret 取自 `settings.jwt_secret`。

---

## 2. 資料模型:`admin_users`

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | autoincrement |
| username | str unique, indexed | 登入帳號 |
| hashed_password | str | argon2 雜湊字串 |
| is_active | bool, default True | 停用旗標 |
| created_at | datetime(timezone), default now | 建立時間 |

- ORM:`app/models/admin_user.py`,`class AdminUser(Base)`,`__tablename__ = "admin_users"`,使用 SQLAlchemy 2.0 `Mapped` / `mapped_column` 型別註記。
- `app/models/__init__.py` 需 `from app.models.admin_user import AdminUser`,讓 Alembic env.py 的 `import app.models` 能偵測到此表。
- **第一個遷移**:`uv run alembic revision --autogenerate -m "create admin_users"` → 產生 `alembic/versions/<rev>_create_admin_users.py` → `uv run alembic upgrade head`。

---

## 3. `core/security.py`(純函式,不依賴 DB/HTTP)

```
hash_password(plain: str) -> str               # pwdlib argon2
verify_password(plain: str, hashed: str) -> bool
create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str
decode_access_token(token: str) -> dict        # 失效/簽章錯 → raise AuthError
```

- 使用單一 `PasswordHash.recommended()`(pwdlib,argon2 後端)實例。
- `create_access_token`:payload = `{"sub": str(subject), "exp": now+delta, "iat": now}`;delta 預設取 `settings.jwt_expire_minutes`。以 `settings.jwt_secret` + `settings.jwt_algorithm` 簽。
- `decode_access_token`:用 PyJWT 解碼;`ExpiredSignatureError` / `InvalidTokenError` → 轉拋領域例外 `AuthError("登入已失效,請重新登入")`。

---

## 4. Data access:`repositories/admin_repo.py`

純資料存取,回傳 ORM model,不含業務判斷:
```
get_by_username(session, username: str) -> AdminUser | None
get_by_id(session, admin_id: int) -> AdminUser | None
add(session, admin: AdminUser) -> AdminUser     # flush 取得 id,不 commit(交易由呼叫端控制)
```

---

## 5. Business:`services/auth_service.py`

```
authenticate(session, username: str, password: str) -> AdminUser
    # 撈帳號 → verify_password → is_active;任一失敗拋 AuthError(統一訊息,不洩漏帳號是否存在)
create_token_for(admin: AdminUser) -> str
    # security.create_access_token(subject=admin.id)
```

---

## 6. Presentation

### `api/deps.py`
- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")`
- `get_current_admin(token = Depends(oauth2_scheme), session = Depends(get_session)) -> AdminUser`
  - `decode_access_token(token)` → 取 `sub`(字串,轉回 `int`)→ `admin_repo.get_by_id` → 檢查存在且 `is_active` → 回 `AdminUser`;任一失敗(解碼失敗 / 帳號不存在 / 已停用 / sub 非數字)拋 `AuthError`(401)。

### `api/routes/admin_auth.py`(`APIRouter(prefix="/api/admin/auth")`)
| 方法 | 路徑 | 依賴 | 回應 |
|------|------|------|------|
| POST | `/login` | `OAuth2PasswordRequestForm` + session | `Token{access_token, token_type:"bearer"}` |
| GET | `/me` | `get_current_admin` | `AdminRead{id, username, is_active}` |

- 在 `app/main.py` 的 `create_app()` 內 `app.include_router(admin_auth.router)`。

### `schemas/admin.py`
```
class Token(BaseModel):        access_token: str; token_type: str = "bearer"
class AdminRead(BaseModel):    id: int; username: str; is_active: bool
                               model_config = ConfigDict(from_attributes=True)
```
（不需 LoginRequest:登入走 OAuth2 form。`AdminRead` 不含 `hashed_password`。)

---

## 7. CLI bootstrap:`app/cli.py`

- 入口:`uv run python -m app.cli create-admin --username <name>`(argparse,subcommand `create-admin`)。
- 流程:`getpass` 互動輸入密碼兩次(輸入 + 確認,不一致則報錯)→ 開 async session → `admin_repo.get_by_username` 若已存在 → 印錯誤訊息並以非零碼結束 → 否則 `hash_password` → 建 `AdminUser` → `admin_repo.add` → `commit` → 印成功(顯示 username,不顯示密碼)。
- 核心邏輯抽成可測函式 `async def create_admin(session, username, password) -> AdminUser`(已存在拋 `ValueError`/領域例外),argparse 包裝層另寫;測試針對核心函式。
- 密碼基本檢核:長度至少 8 字元(過短報錯)。

---

## 8. 錯誤處理(含分層重構)
- **重構**:`AppError` 階層(`AppError`/`NotFoundError`/`InsufficientStockError`/`InvalidStatusTransition`/`AuthError`)從 `app/api/errors.py` 移到 `app/core/exceptions.py`。`app/api/errors.py` 改為:`from app.core.exceptions import AppError` + 保留 `register_exception_handlers(app)`。如此 `core/security.py`、`services/auth_service.py` 可 `from app.core.exceptions import AuthError`,不違反「下層不依賴 Presentation」。`tests/test_errors.py` 的 import 同步更新;`app/main.py` 不變(仍從 `app.api.errors` 取 `register_exception_handlers`)。
- 沿用 `AuthError`(→ 401,`{detail, code:"AUTH_ERROR"}`)。
- 登入失敗(帳號不存在 / 密碼錯 / 已停用)一律回相同 401 訊息,不洩漏帳號是否存在。
- 輸入格式錯誤由 FastAPI/Pydantic 自動回 422。

---

## 9. 測試策略(TDD,沿用 Phase 1 async 測試框架)
- **security**(單元,無 DB):`hash_password`/`verify_password` round-trip;錯誤密碼 verify 為 False;`create_access_token`→`decode_access_token` round-trip 取回 `sub`;過期 token → `AuthError`;竄改/亂碼 token → `AuthError`。
- **admin_repo**(用 `db_session`):新增後 `get_by_username`/`get_by_id` 取得;不存在回 None。
- **auth_service**(用 `db_session`):正確帳密 → 回 AdminUser;錯密碼 / 不存在 / 停用 → `AuthError`。
- **login 端點**(用 `client`):正確 → 200 + token;錯誤 → 401。
- **get_current_admin / me**(用 `client`):有效 token → 200 + AdminRead;無 token / 亂碼 / 過期 / 停用帳號 → 401。
- **CLI**(用 `db_session`):`create_admin` 建立成功;重複 username → 報錯;密碼過短 → 報錯。

---

## 10. 檔案異動清單
新增:
- `app/models/admin_user.py`、`app/schemas/admin.py`、`app/repositories/admin_repo.py`、`app/services/auth_service.py`、`app/core/security.py`、`app/api/deps.py`、`app/api/routes/__init__.py`、`app/api/routes/admin_auth.py`、`app/cli.py`
- `alembic/versions/<rev>_create_admin_users.py`(autogenerate)
- 測試:`tests/test_security.py`、`tests/test_admin_repo.py`、`tests/test_auth_service.py`、`tests/test_admin_auth_api.py`、`tests/test_cli.py`

修改:
- `app/models/__init__.py`(匯出 AdminUser)
- `app/main.py`(include admin_auth router)
- `app/api/errors.py`(改為從 `app/core/exceptions.py` import 例外類別,僅保留 handler 註冊)
- `app/core/exceptions.py`(**新增**,承接原本 errors.py 的例外類別)
- `tests/test_errors.py`(import 改自 `app.core.exceptions` / 對應路徑)

---

## 11. 未來擴充(非本階段)
- Refresh token、登入速率限制、管理員角色/權限。
- CLI 增加列表 / 停用 / 改密碼。
- 顧客 LINE Login(另案)。
