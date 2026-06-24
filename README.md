# 妙媽媽果園（miao-fruit-shop）

妙媽媽果園的線上訂購網站。整合 **LINE LIFF**,讓顧客在 LINE 內完成下單,並透過 **LINE Messaging API** 推送訂單通知卡片。後台提供商品規格與訂單管理。

商店頁以單一商品（甘露梨）搭配多規格（SpecCard）呈現,付款採「轉帳匯款」流程。

---

## 技術棧

### 前端（`frontend/`）
- **React 18** + **React Router 7**
- **Vite 8**（開發伺服器與打包,`@vitejs/plugin-react`）
- **@dnd-kit**（後台拖曳排序）
- **LINE LIFF**（在 LINE 內取得使用者身分與下單情境）
- 部署於 **Vercel**

### 後端（`backend/`）
- **Python 3.13** + **FastAPI**
- **Uvicorn**（ASGI server）
- **SQLAlchemy 2.0**（async）+ **asyncpg**（PostgreSQL 驅動）
- **Alembic**（資料庫遷移）
- **Pydantic v2** / **pydantic-settings**（設定與驗證）
- **PyJWT** + **pwdlib[argon2]**（後台管理員驗證）
- **google-cloud-storage**（商品圖片儲存於 GCS）
- **LINE Messaging API**（訂單通知 Flex Message）
- 套件管理採 **uv**;部署於 **GCP Cloud Run**

### 資料庫
- **PostgreSQL 17**（本地以 docker-compose 啟動;正式環境為 Cloud SQL）

### 開發工具
- **pytest** / **pytest-asyncio**（測試）
- **ruff**（lint）、**mypy**（型別檢查,strict）

---

## 專案結構

```
miao-fruit-shop/
├── frontend/              # React + Vite 前端
│   ├── src/
│   └── .env.example
├── backend/               # FastAPI 後端
│   ├── app/
│   │   ├── api/routes/    # API 路由（products / orders / admin_*）
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # 業務邏輯（含 line_service 通知）
│   │   ├── repositories/  # 資料存取
│   │   ├── core/          # 設定、DB、安全性
│   │   ├── cli.py         # 管理指令（建立管理員、建立初始商品）
│   │   └── main.py        # FastAPI app 進入點
│   ├── alembic/           # 資料庫遷移
│   ├── tests/
│   ├── Dockerfile
│   ├── docker-compose.yml # 本地 PostgreSQL + API
│   └── .env.example
└── vercel.json            # 前端 Vercel 部署設定
```

---

## 環境需求

- **Node.js**（建議 18+,用於前端）
- **Python 3.13**
- **uv**（後端套件管理,安裝見 <https://docs.astral.sh/uv/>）
- **Docker** / **Docker Compose**（本地啟動 PostgreSQL,選用）

---

## 後端啟動

### 方式 A：Docker Compose（一鍵起 DB + API,最簡單）

```bash
cd backend
docker compose up --build
```

- API 服務：<http://localhost:8000>
- PostgreSQL：`localhost:5432`（user/pass/db 皆為 `miao`）

> 注意：compose 啟動的 API 容器尚未自動跑遷移,首次仍需執行下方「資料庫遷移」。

### 方式 B：本地 uv 跑 API（搭配 compose 的 db）

1. 啟動資料庫（擇一）：

   ```bash
   cd backend
   docker compose up db        # 只起 PostgreSQL
   ```

2. 安裝相依並設定環境變數：

   ```bash
   cd backend
   uv sync                     # 安裝相依（含 dev 群組）
   cp .env.example .env        # 依需求調整
   ```

3. 套用資料庫遷移：

   ```bash
   uv run alembic upgrade head
   ```

4. （首次）建立初始商品與後台管理員：

   ```bash
   uv run python -m app.cli seed-product
   uv run python -m app.cli create-admin --username admin
   ```

5. 啟動開發伺服器（熱重載）：

   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

   - 健康檢查：<http://localhost:8000/health>
   - 互動式 API 文件：<http://localhost:8000/docs>

### 後端環境變數（`backend/.env`）

| 變數 | 說明 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL 連線字串（`postgresql+asyncpg://...`）。Cloud Run 可改用拆開式 `DB_USER` / `DB_PASSWORD` / `DB_NAME` / `DB_HOST` / `DB_PORT` |
| `JWT_SECRET` | 後台 JWT 簽章密鑰（正式環境務必改成隨機長字串） |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | JWT 演算法與有效時間 |
| `CORS_ORIGINS` | 逗號分隔的允許來源（前端本地與正式網址） |
| `GCS_BUCKET_NAME` / `GCS_CREDENTIALS_B64` | 商品圖片儲存（選填,未設定時圖片 API 回傳 503） |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API token（選填,未設定時不推送訂單通知） |

完整範例見 [backend/.env.example](backend/.env.example)。

---

## 前端啟動

```bash
cd frontend
npm install
cp .env.example .env          # 填入 LIFF ID、API 網址等
npm run dev                    # 開發伺服器，預設 http://localhost:8080
```

其他指令：

```bash
npm run build                  # 打包至 frontend/dist
npm run preview                # 預覽打包結果
```

### 前端環境變數（`frontend/.env`）

| 變數 | 說明 |
| --- | --- |
| `VITE_MIAO_LIFF_ID` | LINE LIFF App ID |
| `VITE_MIAO_API_BASE_URL` | 後端 API 基底網址 |
| `VITE_MIAO_LINE_ADD_FRIEND_URL` | 官方帳號加好友連結（`https://lin.ee/xxxx`） |

完整範例見 [frontend/.env.example](frontend/.env.example)。

---

## 測試與程式碼品質（後端）

```bash
cd backend
uv run pytest                  # 執行測試
uv run ruff check .            # lint
uv run mypy app                # 型別檢查（strict）
```

---

## 部署

- **前端**：Vercel。設定見根目錄 [vercel.json](vercel.json)（建置 `frontend/`、SPA rewrites）。LIFF Endpoint 綁定 Vercel production 固定網址。
- **後端**：GCP Cloud Run,以 [backend/Dockerfile](backend/Dockerfile) 建置容器映像。資料庫使用 Cloud SQL（PostgreSQL）。

> 正式環境一律從 `master` 分支部署,部署前請先確認變更已合併進 `master`。
