# 妙媽媽果園 — 後端服務架構設計

- 日期:2026-06-11
- 狀態:待審核
- 範圍:後端 v1 架構與技術選用

---

## 1. 目標與範圍

為「妙媽媽果園」單一商品多規格的水梨電商建立後端服務,採三層(multi-layer)架構。

### v1 範圍(本次)
- **商品 / 規格 / 庫存管理**:商品與其多個規格的 CRUD、價格與庫存維護。
- **訂單**:接收前端送出的訂單、伺服器端重算金額與驗扣庫存、查詢、單筆讀取。
- **後台管理**:管理員 JWT 登入、訂單狀態管理。

### 不在 v1 範圍(明確排除)
- 金流串接(LINE Pay / 信用卡 / ATM)——訂單僅記錄「付款方式」,不實際收款。
- 出貨通知(LINE / Email)。
- 顧客會員系統——維持**免登入訪客結帳**,訂單直接帶完整收件資訊。
- Refresh token 機制(列為未來擴充)。

### 前提假設(已與使用者確認)
1. 顧客端免登入(訪客結帳)。
2. 金流與通知不納入 v1。
3. 單一商品多規格:商品管理 = 管理那一個商品 + 其多個規格 / 庫存(結構仍支援多商品)。
4. 套件管理使用 uv。

---

## 2. 技術選用(已核可)

### 核心
| 技術 | 版本 | 角色 |
|------|------|------|
| Python | 3.13 | 執行環境 |
| FastAPI | 0.136.3 | Web framework(Presentation 層) |
| SQLAlchemy | 2.0.50 | ORM(Data access 層),採 **async** |
| Pydantic | 2.13.4 (v2) | 資料驗證 / schema |
| PostgreSQL | 17 | 資料庫 |
| asyncpg | 0.31.0 | async PostgreSQL driver |
| Alembic | 1.18.4 | 資料庫 schema 遷移 |
| pydantic-settings | 2.14.1 | 環境變數設定 |
| uvicorn | 0.49.0 | ASGI server |
| PyJWT | 2.13.0 | JWT 簽發 / 驗證 |
| pwdlib[argon2] | pwdlib 0.3.0 / argon2-cffi 25.1.0 | 密碼雜湊(argon2,刻意不用已停更的 passlib) |
| python-multipart | 0.0.32 | 解析 OAuth2 password 登入表單 |

### 開發 / 品質工具
| 技術 | 版本 | 角色 |
|------|------|------|
| uv | 0.11.19 | 套件 / 虛擬環境管理 |
| pytest | 9.0.3 | 測試框架 |
| pytest-asyncio | 1.4.0 | 測試 async 程式 |
| httpx | 0.28.1 | 測試時打 API |
| ruff | 0.15.16 | Linter + formatter |
| mypy | 2.1.0 | 靜態型別檢查 |
| Docker | (已在用) | 容器化 |

---

## 3. 架構分層

### 依賴方向(單向)
```
Presentation (app/api/)
      ↓  呼叫 service,傳 Pydantic DTO
Business logic (app/services/)
      ↓  呼叫 repository,傳 ORM model
Data access (app/repositories/)
      ↓
PostgreSQL (async / asyncpg)
```
下層不可反向依賴上層。`core/`(config、security、database session)為三層共用的基礎設施。

### 各層職責
- **Presentation 層(`app/api/`)**:FastAPI routers 解析請求、回傳 HTTP 狀態;用 Pydantic schema 驗證輸入 / 序列化輸出;`deps.py` 注入 DB session、驗證 JWT 取得管理員。**不含業務規則**。
- **Business logic 層(`app/services/`)**:業務規則(重算金額、驗庫存、扣庫存、訂單狀態轉移);交易邊界(一個 service 方法 = 一個 DB 交易);拋領域例外。**不碰 HTTP、不寫 SQL**。
- **Data access 層(`app/repositories/`)**:只負責 SQLAlchemy 查詢與持久化,回傳 ORM model。**不含業務判斷**。

### 關鍵原則:伺服器是金額與庫存的權威來源
前端送出的金額(小計 / 運費 / 總額)**一律不信任**。建立訂單時,Business 層用 `spec_id + qty` 從 DB 撈當前價格、驗證庫存、自行重算運費 / 貨到付款手續費 / 總額,並產生權威 `order_no`。前端金額僅供不符時參考、不採用。

### 專案結構(分層優先 + Repository)
```
backend/
  app/
    api/                 # Presentation 層
      routes/
        products.py      # 公開:商品讀取
        orders.py        # 公開:建立訂單
        admin_auth.py    # 後台:登入
        admin_products.py# 後台:商品 / 規格管理
        admin_orders.py  # 後台:訂單管理
      deps.py            # 依賴注入(db session、get_current_admin)
      errors.py          # 領域例外 → HTTP 對映(exception handlers)
    services/            # Business logic 層
      auth_service.py
      product_service.py
      order_service.py
    repositories/        # Data access 層
      admin_repo.py
      product_repo.py
      spec_repo.py
      order_repo.py
    models/              # SQLAlchemy ORM models
      admin_user.py
      product.py
      product_spec.py
      order.py
      order_item.py
    schemas/             # Pydantic v2 DTO(請求 / 回應)
      product.py
      order.py
      admin.py
    core/
      config.py          # pydantic-settings
      security.py        # JWT 簽發/驗證、密碼雜湊
      database.py        # async engine / session factory
    main.py              # FastAPI app 組裝(router、CORS、exception handlers)
  alembic/               # 遷移
  tests/
  pyproject.toml         # uv + 依賴
  Dockerfile
  .env.example
```

---

## 4. 資料模型

金額一律用**整數 NT$**(台幣無小數)。

### admin_users
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| username | str unique | 登入帳號 |
| hashed_password | str | argon2 雜湊 |
| is_active | bool | 停用旗標 |
| created_at | datetime | |

### products
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| slug | str unique | 識別字串 |
| name | str | 商品名(甘露梨) |
| sub | str | 副標(拉丁名 · 標語) |
| description | text | 描述 |
| image | str | 圖片路徑 |
| season | str | 產季文字 |
| tag | str nullable | 標籤(珍稀) |
| tag_color | str nullable | 標籤色 |
| is_active | bool | |
| created_at / updated_at | datetime | |

### product_specs
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| product_id | int FK→products | |
| label | str | 規格名(5 台斤家庭箱) |
| qty_text | str | 內容描述(6–8 顆 · 5 台斤) |
| price | int | NT$ |
| stock_qty | int | 庫存數量(可扣減) |
| low_stock_threshold | int | 低庫存門檻,預設 3 |
| note | str nullable | 備註 |
| sort_order | int | 排序 |
| is_active | bool | 軟刪除用 |

> `stock_status`(in / low / out)**不入庫**,由回應 schema 依 `stock_qty` 與 `low_stock_threshold` 推導:`stock_qty<=0 → out`、`<=threshold → low`、其餘 `in`。

### orders
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| order_no | str unique | 伺服器產生,格式 `MM-XXXXXX` |
| status | enum | 見下方狀態定義 |
| customer_name / customer_phone / customer_email | str | email 可空 |
| ship_zipcode / ship_city / ship_district / ship_street | str | 收件地址組成 |
| preferred_date | date | 希望送達日 |
| delivery_window | str | 送達時段(不指定 / 上午 / 下午) |
| payment_method | str | linepay / card / atm / cod |
| note | text nullable | 備註 |
| subtotal / shipping_fee / cod_fee / total | int | 伺服器寫入 |
| created_at / updated_at | datetime | |

### order_items
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| order_id | int FK→orders | |
| product_id | int | |
| spec_id | int nullable | 規格日後刪除時保留歷史 |
| product_name | str | **快照** |
| spec_label | str | **快照** |
| unit_price | int | **快照** |
| qty | int | |
| line_total | int | unit_price × qty |

> 明細快照商品名 / 規格名 / 單價,日後改價或下架規格不影響歷史訂單。

### 訂單狀態(enum)與轉移規則
| 狀態 | 中文 | 說明 |
|------|------|------|
| `pending_payment` | 待付款 | 預付方式(linepay / card / atm)的初始態 |
| `pending` | 待出貨 | 貨到付款(cod)初始態,或預付確認收款後進入 |
| `shipped` | 已出貨 | |
| `completed` | 已完成 | |
| `cancelled` | 已取消 | 可從任一非完成態轉入 |

**建立訂單時的初始態**:`payment_method == cod` → `pending`;其餘 → `pending_payment`。

**合法轉移**(由 Business 層驗證,違者拋 `InvalidStatusTransition`):
```
pending_payment → pending | cancelled
pending         → shipped | cancelled
shipped         → completed | cancelled
completed       → (終態)
cancelled       → (終態)
```

---

## 5. API 端點

### 公開(無需驗證,商店前台用)
| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/api/products` | 取啟用中的商品 + 規格(附推導 `stock_status`、`stock_qty`),取代前端寫死的 `data.js` |
| POST | `/api/orders` | 建立訂單。請求帶 `items:[{spec_id, qty}]`、收件人、配送、付款方式、備註;伺服器重算金額、驗 / 扣庫存、回傳權威 `order_no` 與金額 |

### 後台(需 JWT,前綴 `/api/admin`)
| 方法 | 路徑 | 用途 |
|------|------|------|
| POST | `/auth/login` | OAuth2 password form(帳號 + 密碼)→ access token |
| GET | `/auth/me` | 取當前管理員資訊 |
| GET | `/products` · GET `/products/{id}` | 商品列表 / 單筆 |
| POST | `/products` · PATCH `/products/{id}` | 新增 / 修改商品 |
| POST | `/products/{id}/specs` · PATCH `/specs/{id}` | 新增規格 / 改規格(價格、庫存、備註、啟用) |
| DELETE | `/specs/{id}` | 下架規格(軟刪除 `is_active=false`) |
| GET | `/orders` | 訂單列表(可依 status 篩選、分頁) |
| GET | `/orders/{order_no}` | 單筆訂單明細 |
| PATCH | `/orders/{order_no}/status` | 變更訂單狀態(伺服器驗證轉移合法性) |

### 建立訂單請求 / 回應(摘要)
請求(前端送):
```json
{
  "customer": { "name": "...", "phone": "...", "email": "..." },
  "shipping": {
    "zipcode": "...", "city": "...", "district": "...", "street": "...",
    "preferred_date": "2026-10-12", "delivery_window": "am"
  },
  "items": [ { "spec_id": 2, "qty": 1 } ],
  "payment_method": "linepay",
  "note": "..."
}
```
回應(伺服器算):
```json
{
  "order_no": "MM-AB12CD",
  "status": "pending_payment",
  "items": [ { "product_name": "甘露梨", "spec_label": "5 台斤家庭箱", "unit_price": 1880, "qty": 1, "line_total": 1880 } ],
  "subtotal": 1880, "shipping_fee": 150, "cod_fee": 0, "total": 2030,
  "created_at": "..."
}
```

---

## 6. JWT 登入流程
1. `POST /auth/login` 收帳密 → Data access 撈 `admin_users` → pwdlib argon2 驗證密碼。
2. 通過則簽發 JWT(HS256,secret 來自設定,`sub=admin_id`,含 `exp`,效期可設定,預設 8 小時)。
3. 受保護路由透過 `deps.py` 的 `get_current_admin`:解析 `Authorization: Bearer`、解碼、載入管理員、檢查 `is_active`。
4. v1 不做 refresh token(YAGNI),列為未來擴充。

---

## 7. 錯誤處理
- Business 層拋**領域例外**:`NotFoundError`、`InsufficientStockError`、`InvalidStatusTransition`、`AuthError`(不碰 HTTP)。
- Presentation 層(`api/errors.py`)用 FastAPI exception handler 將領域例外對映成 HTTP 狀態碼,回應格式固定:
  ```json
  { "detail": "庫存不足", "code": "INSUFFICIENT_STOCK" }
  ```
- 對映:`NotFoundError→404`、`InsufficientStockError→409`、`InvalidStatusTransition→409`、`AuthError→401`。
- 輸入驗證錯誤由 Pydantic 自動回 422。

---

## 8. 交易、CORS、設定
- **交易邊界**:一個 service 方法 = 一個 DB 交易。建立訂單的「驗庫存 → 扣庫存 → 寫訂單」在同一交易內,確保一致性;失敗則整筆 rollback。
- **CORS**:前端與後端不同源,加 CORS middleware,允許來源由設定 `CORS_ORIGINS` 控制(本機預覽 `http://localhost:8080`、Netlify 網域)。
- **設定**(pydantic-settings 讀 `.env`):`DATABASE_URL`、`JWT_SECRET`、`JWT_EXPIRE_MINUTES`、`JWT_ALGORITHM`、`CORS_ORIGINS`。

---

## 9. 測試策略
- `pytest` + `pytest-asyncio` + `httpx.AsyncClient`(走 ASGITransport,不需真的開 port)。
- 獨立測試資料庫,每個測試包在交易內、結束 rollback,保持隔離。
- **Business 層單元測試**:重算金額、扣庫存、狀態轉移規則。
- **API 層整合測試**:端到端打端點(含 JWT 受保護路由)。
- 實作時走 TDD(先寫測試,再寫實作)。

---

## 10. 與前端的對接調整(後續)
- 前端 `data.js` 的商品資料改由 `GET /api/products` 提供(`stock` 文字狀態改用 API 推導的 `stock_status`)。
- 前端 `Cart.jsx` 的 `submitOrder(order)` stub 改為 `POST /api/orders`,並改送 `items:[{spec_id, qty}]`(不再自行算金額、不自帶 order id)。
- 這些前端改動屬後端完成後的整合工作,**不在本後端 spec 的實作範圍**。

---

## 11. 未來擴充(非 v1)
- 金流串接(LINE Pay / 信用卡 / ATM 虛擬帳號)。
- 出貨通知(LINE / Email)。
- Refresh token / 管理員角色權限。
- 多商品目錄(結構已預留)。
