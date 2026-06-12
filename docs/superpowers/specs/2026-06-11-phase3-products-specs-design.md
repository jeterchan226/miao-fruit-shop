# 妙媽媽果園 — Phase 3:商品 / 規格(Products & Specs)設計

- 日期:2026-06-11
- 狀態:已審核通過(使用者確認;依回饋移除 `products.sub` 欄位)
- 上層 spec:`docs/superpowers/specs/2026-06-11-backend-architecture-design.md`(第 4、5 節)
- 前置:Phase 1 地基 + Phase 2 後台驗證已完成(`get_current_admin` 可用)

---

## 1. 目標與範圍

在現有後端加入商品與規格的管理與公開查詢,讓前端商店頁改由 API 取得商品資料(取代寫死的 `data.js`)。

### 本階段範圍
- `products` 與 `product_specs` ORM model + **第二個 Alembic 遷移**(autogenerate)。
- `repositories/product_repo.py`、`repositories/spec_repo.py`(資料存取)。
- `services/product_service.py`(列出啟用商品+規格、推導 stock_status、後台更新商品、規格 CRUD)。
- `schemas/product.py`(公開與後台兩組 schema)。
- **公開** `GET /api/products`(取代前端 data.js)。
- **後台**(以 `get_current_admin` 保護)商品更新 + 規格 CRUD。
- `cli.py` 新增 `seed-product` 指令(bootstrap 單一商品 + 現有 3 規格)。
- 對應測試(TDD)。

### 不在本階段(明確排除)
- **商品的建立 / 刪除端點**(單一商品前提:商品用 seed 建立,後台只能更新)。
- 庫存扣減(Phase 4 訂單建立時才扣)。
- 分頁、搜尋、多商品目錄(結構支援多商品,但本階段不需要)。
- 前端串接本 API(後端完成後另行整合,不在本後端 spec 範圍)。

### 已確認決策
1. **商品 = Seed + 只能更新**:`uv run python -m app.cli seed-product` 建立甘露梨商品 + 3 規格;商品已存在則報錯中止。後台只提供商品 UPDATE,不提供 create/delete 商品端點。
2. **規格 = 完整 CRUD**:後台可新增 / 修改 / 下架(軟刪除)規格。前端商店頁「卡片數 = 啟用中的規格數」(一規格一卡,SpecCard)。
3. **公開 API 不揭露精確庫存數量**:只回傳推導的 `stock_status`(in / low / out);精確 `stock_qty` 只有後台看得到。

---

## 2. 資料模型

### products
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| slug | str unique, indexed | 識別字串(例 `kanro`) |
| name | str | 商品名(甘露梨) |
| description | text | 描述 |
| image | str | 圖片路徑 |
| season | str | 產季文字 |
| tag | str nullable | 標籤(珍稀) |
| tag_color | str nullable | 標籤色(red) |
| is_active | bool, default True | 商品停售旗標 |
| created_at / updated_at | datetime(tz), server_default now / onupdate now | |

### product_specs
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| product_id | int FK→products.id, indexed | |
| label | str | 規格名(`5 台斤家庭箱`) |
| qty_text | str | 內容描述(`6–8 顆 · 5 台斤`) |
| price | int | NT$(整數) |
| stock_qty | int | 精確庫存數量 |
| low_stock_threshold | int, default 3 | 低庫存門檻 |
| note | str nullable | 自由文字備註(`老客戶限定`) |
| sort_order | int, default 0 | 規格排序 |
| is_active | bool, default True | 軟刪除 / 下架 |

- ORM 採 SQLAlchemy 2.0 `Mapped` / `mapped_column`。`Product` 與 `ProductSpec` 各一檔,`app/models/__init__.py` 匯出兩者(供 Alembic autogenerate)。
- `product_specs.product_id` 設 `ForeignKey("products.id")`;`Product` 可選擇性加 `specs` relationship(見 §6 取捨)。
- **第二個遷移**:`alembic revision --autogenerate -m "create products and product_specs"` → `alembic upgrade head`。

---

## 3. 庫存狀態推導(stock_status)

集中於 service 層的純函式(可單獨測):
```
derive_stock_status(stock_qty, low_stock_threshold) -> "in" | "low" | "out"
    stock_qty <= 0                      → "out"   (售完 / 預購)
    stock_qty <= low_stock_threshold    → "low"   (庫存極少)
    否則                                 → "in"    (現貨供應)
```
公開 schema 帶 `stock_status`(+ `note`),**不**帶 `stock_qty`。後台 schema 帶 `stock_qty`(+ `low_stock_threshold`)。

---

## 4. Schema(`schemas/product.py`)

**公開(顧客)**
- `PublicSpecRead`:`id`, `label`, `qty_text`, `price`, `stock_status`(str), `note`(str | None)。**不含** `stock_qty`。
- `PublicProductRead`:`id`, `slug`, `name`, `description`, `image`, `season`, `tag`, `tag_color`, `specs: list[PublicSpecRead]`。

**後台**
- `AdminSpecRead`:公開欄位 + `stock_qty`, `low_stock_threshold`, `sort_order`, `is_active`。
- `AdminProductRead`:商品欄位 + `is_active` + `specs: list[AdminSpecRead]`(含停用規格)。
- `ProductUpdate`:所有商品欄位皆 Optional(部分更新):`name`, `description`, `image`, `season`, `tag`, `tag_color`, `is_active`。
- `SpecCreate`:`label`, `qty_text`, `price`, `stock_qty`, `low_stock_threshold`(預設 3), `note`(可空), `sort_order`(預設 0)。
- `SpecUpdate`:上述欄位皆 Optional(部分更新)+ `is_active`。

`stock_status` 不入庫,由 service 在組裝回應時用 `derive_stock_status` 計算填入。

---

## 5. 端點

### 公開(無需驗證)
| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/api/products` | 列出 `is_active=True` 的商品,每個帶 `is_active=True` 的規格(依 `sort_order, id`),規格含推導 `stock_status` + `note`,不含 `stock_qty`。回 `list[PublicProductRead]` |

### 後台(prefix `/api/admin`,`Depends(get_current_admin)`)
| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/products` | 完整資料(含停用商品/規格、含 `stock_qty`)→ `list[AdminProductRead]` |
| PATCH | `/products/{product_id}` | 部分更新商品欄位;找不到→404 |
| POST | `/products/{product_id}/specs` | 新增規格;商品不存在→404 |
| PATCH | `/specs/{spec_id}` | 部分更新規格;找不到→404 |
| DELETE | `/specs/{spec_id}` | 軟刪除規格(`is_active=False`);找不到→404 |

不提供商品 create / delete 端點。

---

## 6. 三層職責與取捨

- **Data access**:`product_repo`(`list_active`, `list_all`, `get_by_id`, `get_by_slug`, `add`)、`spec_repo`(`get_by_id`, `add`, `list_for_product`)。回傳 ORM model。
- **Business**:`product_service` 負責「只列啟用」「組裝 specs 並推導 stock_status」「更新商品」「規格 CRUD(含找不到拋 NotFoundError)」「軟刪除」。交易在 service 內 commit。
- **Presentation**:routes 解析請求、注入 `get_current_admin`(後台)、回對應 schema。
- **relationship 取捨**:`Product.specs` 用 `relationship`(`lazy="selectin"`)方便一次載入;讀取啟用規格時於 service 過濾 `is_active` 並排序。若不使用 relationship,則 service 改用 `spec_repo.list_for_product`。**採 selectin relationship**(較少 round-trip、程式清楚)。

---

## 7. 錯誤處理
- 找不到商品 / 規格 → `NotFoundError`(404,`{detail, code:"NOT_FOUND"}`)。
- 後台端點未帶有效 token → 401(`AuthError`,沿用 `get_current_admin`)。
- 輸入驗證錯誤 → Pydantic 422。

---

## 8. CLI:`seed-product`
- `uv run python -m app.cli seed-product`:建立甘露梨商品 + 3 個規格(對應前端現有資料:`2 粒精緻禮盒` / `5 台斤家庭箱` / `10 台斤大箱`,價格 880 / 1880 / 3580)。具體 `stock_qty` 初始值由實作計畫定義(其中 `5 台斤家庭箱` 設為 ≤ 門檻以示範 `low` 狀態,其餘設為充足以示範 `in`),`note` 對應現有 data.js(`蜜糖之味` / `剩 3 箱` / `老客戶限定`)。
- 若 slug `kanro` 已存在 → 報錯中止(與 `create-admin` 一致)。
- 核心邏輯抽成可測函式 `async def seed_product(session) -> Product`(已存在拋 `ValueError`);argparse 子指令 `seed-product` 包裝。

---

## 9. 測試策略(TDD)
- **derive_stock_status**(純單元):邊界 `0→out`、`<=門檻→low`、`>門檻→in`、負數→out。
- **product_repo / spec_repo**(db_session):新增、查詢、list_active 只回啟用、get_by_slug。
- **product_service**(db_session):列出只含啟用商品/規格且 specs 依 sort_order、stock_status 正確;更新商品欄位;新增/更新規格;軟刪除後不出現在公開列表;找不到→NotFoundError。
- **公開 `GET /api/products`**(client):回啟用資料、規格含 stock_status、**回應 JSON 不含 `stock_qty`**(明確斷言)。
- **後台端點**(client):無 token→401;帶 token 可 GET(含 stock_qty)、PATCH 商品、POST/PATCH/DELETE 規格;不存在 id→404。
- **seed-product CLI**(db_session):`seed_product` 建立商品+3 規格;重複→ValueError。

---

## 10. 檔案異動清單
新增:
- `app/models/product.py`、`app/models/product_spec.py`
- `app/schemas/product.py`
- `app/repositories/product_repo.py`、`app/repositories/spec_repo.py`
- `app/services/product_service.py`
- `app/api/routes/products.py`、`app/api/routes/admin_products.py`
- `alembic/versions/<rev>_create_products_and_product_specs.py`(autogenerate)
- 測試:`tests/test_stock_status.py`、`tests/test_product_repo.py`、`tests/test_spec_repo.py`、`tests/test_product_service.py`、`tests/test_products_api.py`、`tests/test_admin_products_api.py`、`tests/test_seed_product_cli.py`

修改:
- `app/models/__init__.py`(匯出 Product、ProductSpec)
- `app/main.py`(include `products` 與 `admin_products` router)
- `app/cli.py`(新增 `seed-product` 子指令 + `seed_product` 函式)

---

## 11. 未來擴充(非本階段)
- 庫存扣減(Phase 4 訂單)。
- 前端 `data.js` → `GET /api/products` 串接、`submitOrder` → `POST /api/orders`(Phase 4 後)。
- 多商品目錄、商品 create/delete、分頁 / 搜尋。
- 商品圖片上傳(目前 image 為路徑字串)。
