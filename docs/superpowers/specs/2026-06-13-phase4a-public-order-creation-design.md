# 妙媽媽果園 — Phase 4a:公開下單(Public Order Creation)設計

- 日期:2026-06-13
- 狀態:草稿(待使用者審核)
- 上層 spec:`docs/superpowers/specs/2026-06-11-backend-architecture-design.md`(第 4、5、7 節)
- 前置:Phase 1 地基 + Phase 2 後台驗證 + Phase 3 商品/規格已完成(`GET /api/products`、`product_specs` 可用)
- 後續:Phase 4b(後台訂單管理:列表/明細/改狀態)另開 spec/plan,沿用本階段建立的 `orders` / `order_items` 模型。

---

## 1. 目標與範圍

實作顧客下單的公開端點 `POST /api/orders`:前端送購物車內容 + 收件/付款資訊,伺服器**權威重算金額、行鎖驗證並扣庫存、產生權威 `order_no`**,回傳成交結果。

### 本階段範圍
- `orders` 與 `order_items` ORM model + **第三個 Alembic 遷移**(autogenerate)。
- `repositories/order_repo.py`(`add`、`get_by_order_no`);擴充 `spec_repo` 加 `get_for_update`(行鎖讀取)。
- `services/order_service.py`:單一交易內完成「鎖規格 → 重算金額 → 價格確認 → 驗/扣庫存 → 產 order_no → 建單」;金額推導純函式;初始狀態決策。
- `schemas/order.py`:`OrderCreate`(請求)、`OrderRead`(回應)、`PriceChangedResponse`(409 回應體)。
- `core/exceptions.py` 新增 `PriceChangedError`;`api/errors.py` 對映 → 409。
- `core/constants.py`(新檔)集中金額常數。
- 公開 `POST /api/orders`(201)。
- 對應測試(TDD)。

### 不在本階段(明確排除)
- **後台訂單管理**(列表/明細/改狀態):Phase 4b。
- **真實金流**:不串 LINE Pay / 信用卡 / ATM 金流 API;v1 只記錄 `payment_method` 並依規則設初始狀態。
- **顧客查單端點**(公開 `GET /api/orders/{order_no}`):前端目前不需要,列未來擴充。
- **商品讀取快取層**:單商品 + 3 規格,query 極輕,依 YAGNI 現階段不做;未來有流量需求時另開 phase(屬讀取路徑)。
- 前端串接(`submitOrder` → `fetch('/api/orders')`):後端完成後另行整合,不在本後端 spec 範圍。

### 已確認決策
1. **拆 4a / 4b**:本階段只做公開下單;後台訂單管理為 4b。
2. **付款只記錄方式 + 設初始狀態**:不串真實金流。`payment_method == "cod" → pending`;其餘(linepay/card/atm)→ `pending_payment`。
3. **庫存以 DB 行鎖(`SELECT ... FOR UPDATE`)防超賣**:在單一交易內鎖規格列、驗證、扣減。
4. **價格確認**:前端送 `expected_total`(畫面顯示給使用者的合計)。伺服器重算後不符 → 回 `409 PRICE_CHANGED` + 新金額明細,**不建單**;使用者重新確認後再送一次。保證「使用者看到的金額 = 付款金額」。
5. **伺服器權威金額**:前端只送 `items:[{spec_id, qty}]`,不送單價;伺服器以 `spec_id` 查 DB 當下 `price` 重算。

---

## 2. 資料模型

金額一律用**整數 NT$**(無小數)。

### orders
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| order_no | str unique, indexed | 伺服器產生,格式 `MM-XXXXXX`(見 §5) |
| status | str(enum 值) | 初始態見 §6;轉移規則由 4b 使用 |
| customer_name | str | |
| customer_phone | str | |
| customer_email | str nullable | 可空 |
| ship_zipcode | str | |
| ship_city | str | |
| ship_district | str | |
| ship_street | str | |
| preferred_date | date | 希望送達日 |
| delivery_window | str | `any` / `am` / `pm` |
| payment_method | str | `linepay` / `card` / `atm` / `cod` |
| note | text nullable | 備註 |
| subtotal | int | 伺服器寫入 |
| shipping_fee | int | 伺服器寫入 |
| cod_fee | int | 伺服器寫入 |
| total | int | 伺服器寫入 |
| created_at / updated_at | datetime(tz), server_default now / onupdate now | |

### order_items
| 欄位 | 型別 | 說明 |
|------|------|------|
| id | int PK | |
| order_id | int FK→orders.id, indexed | |
| product_id | int | 下單當下的商品 id |
| spec_id | int nullable | 規格日後刪除仍保留歷史 |
| product_name | str | **快照** |
| spec_label | str | **快照** |
| unit_price | int | **快照**(下單當下單價) |
| qty | int | |
| line_total | int | unit_price × qty |

> 明細**快照**商品名 / 規格名 / 單價;日後改價或下架規格,不影響歷史訂單。
> `Order.items` 用 `relationship`(`lazy="selectin"`, `cascade="all, delete-orphan"`, `order_by` 依 id)。
> `app/models/__init__.py` 匯出 `Order`、`OrderItem`(供 Alembic autogenerate)。
> **第三個遷移**:`alembic revision --autogenerate -m "create orders and order_items"` → `alembic upgrade head`。

### 訂單狀態(本階段只用初始態,完整狀態機在 4b)
`pending_payment`(待付款)、`pending`(待確認)、`confirmed`、`shipping`、`delivered`、`cancelled`。本階段只負責**寫入初始態**;狀態轉移驗證在 4b。

---

## 3. 金額計算(伺服器權威)

集中於 service 層的純函式,常數放 `app/core/constants.py`:
```
FREE_SHIPPING_THRESHOLD = 5000   # 含以上免運
SHIPPING_FEE            = 150
COD_FEE                 = 30
```
規則(與前端 `Cart.jsx` 對齊):
```
subtotal      = Σ (spec.price × qty)              # 以 DB 當下 price
shipping_fee  = 0  if subtotal >= 5000  else 150
cod_fee       = 30 if payment_method == "cod" else 0
total         = subtotal + shipping_fee + cod_fee
```
- 前端**不送任何價格**,只送 `items:[{spec_id, qty}]`;單價一律由伺服器以 `spec_id` 查 DB。
- `subtotal == 0`(空 items)由 Pydantic 擋下(items 需非空、qty ≥ 1)。

---

## 4. 價格確認流程(保證看到的 = 付的)

1. 前端送單時附 `expected_total`(畫面顯示給使用者的訂單合計)。
2. 伺服器在交易內重算權威 `total`。
3. 比對:
   - `expected_total == total` → 正常建單(使用者付的就是他確認過的)。
   - `expected_total != total` → **不建單**,拋 `PriceChangedError` → `409`,回應 `code: "PRICE_CHANGED"` + 新金額明細(`subtotal`/`shipping_fee`/`cod_fee`/`total`),前端提示「商品價格已更新:原 → 現」,使用者重新確認後再送一次。
- 設計理由:伺服器權威(安全/正確)+ 不默默改價(體驗)。不一致時**明確擋下**而非悄悄換價。

---

## 5. `order_no` 產生

- 格式 `MM-XXXXXX`:前綴 `MM-` + 6 碼,字母表去除易混淆字元(無 `0/O/1/I`,例 `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`)。
- 伺服器隨機產生;寫入若違反 `order_no` unique 約束 → 重產重試(上限數次,例 5 次,皆失敗則拋錯)。
- 前端那組 `MM-<timestamp>` 僅本地佔位;**以伺服器回傳的 `order_no` 為準**。

---

## 6. 初始狀態

- `payment_method == "cod"` → `pending`(待出貨,貨到付款)。
- 其餘(`linepay` / `card` / `atm`)→ `pending_payment`(待付款)。
- v1 不串真實金流;狀態之後由後台(4b)推進。

---

## 7. Schema(`schemas/order.py`)

**請求**
- `OrderItemCreate`:`spec_id`(int)、`qty`(int, ge=1)。
- `OrderCreate`:
  - `customer`:`name`、`phone`、`email`(可空)
  - `shipping`:`zipcode`、`city`、`district`、`street`、`preferred_date`(date)、`delivery_window`(`Literal["any","am","pm"]`)
  - `items`:`list[OrderItemCreate]`(min_length=1)
  - `payment_method`:`Literal["linepay","card","atm","cod"]`
  - `note`:str | None
  - `expected_total`:int(ge=0)
  - `extra="forbid"`

**回應**
- `OrderItemRead`:`product_name`、`spec_label`、`unit_price`、`qty`、`line_total`。
- `OrderRead`:`order_no`、`status`、`items: list[OrderItemRead]`、`subtotal`、`shipping_fee`、`cod_fee`、`total`、`created_at`。
- `PriceChangedResponse`(409 body 文件用):`detail`、`code="PRICE_CHANGED"`、`subtotal`、`shipping_fee`、`cod_fee`、`total`。

> 巢狀 `customer` / `shipping` 沿用前端送出的結構(見 `Cart.jsx` 的 order 物件),service 攤平寫入 `orders` 欄位。

---

## 8. 端點

### 公開(無需驗證)
| 方法 | 路徑 | 用途 |
|------|------|------|
| POST | `/api/orders` | 建立訂單。請求帶 `items:[{spec_id, qty}]`、收件人、配送、付款方式、備註、`expected_total`;伺服器重算金額、價格確認、行鎖驗/扣庫存、產 `order_no`、建單。成功 → **201** + `OrderRead`。 |

---

## 9. 三層職責與取捨

- **Data access**:
  - `order_repo`:`add(session, order)`(flush,不 commit)、`get_by_order_no(session, order_no)`。
  - `spec_repo` 擴充:`get_for_update(session, spec_id)` → `SELECT ... FOR UPDATE`(行鎖,回 ORM 或 None)。
- **Business**(`order_service.create_order`):於**單一交易**內依序——
  1. 對每個 `spec_id` `get_for_update` 鎖列;不存在或 `is_active=False` → `NotFoundError`。
  2. 以鎖到的 spec 重算 `subtotal`/`shipping_fee`/`cod_fee`/`total`(純函式 `compute_amounts`)。
  3. 價格確認:`total != expected_total` → `PriceChangedError`(帶新明細)。
  4. 庫存:任一 `spec.stock_qty < qty` → `InsufficientStockError`。
  5. 扣庫存(`stock_qty -= qty`)、決定初始狀態、產 `order_no`(重試)、建立 `Order` + `OrderItem`(快照)、`commit`。
  - 任一例外 → 交易回滾,**不扣庫存、不建單**。
- **Presentation**:`POST /api/orders` 解析 `OrderCreate`、呼叫 service、回 `OrderRead`(201)。

> 檢查順序:存在/啟用 → 價格確認 → 庫存。價格確認先於庫存,確保「價格已變」優先告知(避免使用者以為是庫存問題)。

---

## 10. 錯誤處理

| 情況 | 例外 | HTTP | code |
|------|------|------|------|
| 規格不存在 / 已下架 | `NotFoundError` | 404 | `NOT_FOUND` |
| 價格與 `expected_total` 不符 | `PriceChangedError` | 409 | `PRICE_CHANGED`(+ 新明細) |
| 庫存不足 | `InsufficientStockError` | 409 | `INSUFFICIENT_STOCK` |
| 輸入驗證錯誤 | Pydantic | 422 | — |

> `PriceChangedError` 為本階段新增;`api/errors.py` 的 handler 對映為 409,並在 body 附 `subtotal/shipping_fee/cod_fee/total`(供前端直接顯示新合計,免再打一次 API)。其餘維持 `{detail, code}` 格式。

---

## 11. 測試策略(TDD)

- **compute_amounts**(純單元):免運門檻邊界(4999→150、5000→0)、COD 手續費(cod→30、其餘→0)、total 加總。
- **初始狀態決策**:`cod → pending`、其餘 → `pending_payment`。
- **order_no 格式**:符合 `MM-` + 6 碼字母表。
- **order_service**(db_session):
  - 成功建單:扣庫存正確、明細快照單價/品名/規格、回權威金額與初始狀態。
  - 價格不符:拋 `PriceChangedError`,且**庫存未扣、未建單**(交易回滾)。
  - 庫存不足:拋 `InsufficientStockError`,且**庫存未扣、未建單**。
  - 未知 / 停用 spec → `NotFoundError`。
- **公開 `POST /api/orders`**(client):
  - 201 回 `order_no`(格式)、權威金額、初始狀態、明細快照。
  - 價格不符 → 409 `PRICE_CHANGED` + 新明細。
  - 庫存不足 → 409 `INSUFFICIENT_STOCK`。
  - 缺欄位 / 空 items / qty<1 / 非法 enum → 422。
  - **金額由伺服器算**:即使前端(不送價)期望錯誤的 `expected_total` 也無法以錯價成交(回 409)。

> 並發行鎖(`SELECT FOR UPDATE`)的真實競態不易在單元測試穩定重現;以正確性測試(扣減正確、不足回滾)涵蓋,鎖機制由實作保證,必要時於計畫補一個序列化雙下單測試。

---

## 12. 檔案異動清單

新增:
- `app/models/order.py`、`app/models/order_item.py`
- `app/schemas/order.py`
- `app/repositories/order_repo.py`
- `app/services/order_service.py`
- `app/api/routes/orders.py`
- `app/core/constants.py`
- `alembic/versions/<rev>_create_orders_and_order_items.py`(autogenerate)
- 測試:`tests/test_order_amounts.py`、`tests/test_order_service.py`、`tests/test_orders_api.py`(視需要再加 `test_order_no.py`)

修改:
- `app/models/__init__.py`(匯出 Order、OrderItem)
- `app/repositories/spec_repo.py`(加 `get_for_update`)
- `app/core/exceptions.py`(加 `PriceChangedError`)
- `app/api/errors.py`(對映 `PriceChangedError` → 409)
- `app/main.py`(include `orders` router)

---

## 13. 未來擴充(非本階段)

- **Phase 4b**:後台訂單列表(可依 status 篩選、分頁)、單筆明細、改狀態(伺服器驗證合法轉移)。
- 真實金流(LINE Pay / 信用卡 / ATM)整合 + webhook。
- 顧客查單端點(公開 `GET /api/orders/{order_no}`)。
- 商品讀取快取層(cache-aside + 寫入失效),於有流量需求時。
- 前端 `submitOrder` → `POST /api/orders` 串接、`data.js` → `GET /api/products`。
