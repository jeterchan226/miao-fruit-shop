# 訂購單三項規則上線 — 設計文件

日期：2026-07-14
狀態：待審核

## 背景

實體訂購單（甘露梨目錄表）有三項規則需反映到網頁商店：

1. 同住址滿 $3000 免運
2. 運費分級：一層 $130 / 二層 $150 / 三層 $180
3. 2 粒裝規格須以「雙數」單位購買（2、4、6 箱）

現況：前端 `frontend/src/Cart.jsx` 與後端 `backend/app/core/constants.py` 各自寫死免運門檻 5000、單一運費 150，兩邊須同步。後端 `create_order` 會用 `expected_total` 比對，若前後端算的總額不一致會回 `PRICE_CHANGED` 擋單，因此運費邏輯前後端必須一致。

## 決策（已與使用者確認）

- **運費自動計算**（非「待確認」）。
- **層數公式**：
  - 非 2 粒裝：每箱 = 1 層
  - 2 粒裝：每 2 箱 = 1 層（故須雙數）
  - `總層數 = 非2粒箱數 + (2粒箱數 ÷ 2)`
- **運費**：`subtotal >= 3000 ? 0 : {1:130, 2:150, 3:180}[min(層數, 3)]`
- **超過 3 層不特別處理**：達 4 層時 subtotal 必已超過 $3000 而免運，故 `>3` 一律以 $180 計（保險 fallback）。
- 2 粒裝以布林 tag `is_two_pack` 標記，全端打通。
- Admin 規格表單提供「2 粒裝」勾選框。
- tag 命名：後端 `is_two_pack`、前端 `isTwoPack`。
- 說明文字（運費分級 + 同住址滿 $3000 免運）放購物車與 Notices 兩處。

## 範圍

三塊變更，橫跨 DB / 後端 / 前端。

### A. 2 粒裝 tag + 雙數購買

**資料流（新增一個布林 tag，一路打通）**

| 層 | 檔案 | 變更 |
|----|------|------|
| DB model | `backend/app/models/product_spec.py` | 新增 `is_two_pack: Mapped[bool] = mapped_column(default=False)` |
| Migration | `backend/alembic/versions/*` | `add_is_two_pack_to_product_specs`；`add_column` 帶 `server_default='0'`（既有列安全），可於升級後移除 server_default |
| Schema | `backend/app/schemas/product.py` | `PublicSpecRead` / `AdminSpecRead` / `SpecCreate` / `SpecUpdate` 各加 `is_two_pack`（Create 預設 False、Update 為 `bool \| None`） |
| Service | `backend/app/services/product_service.py` | `_to_public_spec` / `_to_admin_spec` 帶 `is_two_pack=s.is_two_pack` |
| 前端 API | `frontend/src/api.js` | `normalizeProduct` 的 spec map 加 `isTwoPack: spec.is_two_pack` |
| SpecCard | `frontend/src/SpecCard.jsx` | 若 `spec.isTwoPack`：qty 最小 2、預設 2、±2 遞增；顯示「請以雙數（2、4、6…）購買」提示 |
| Cart item | `frontend/src/App.jsx` | `addToCart` 的 cart 物件帶 `isTwoPack: spec.isTwoPack` |
| Cart 列 | `frontend/src/Cart.jsx` `CartItem` | 該品項加減 ±2、最小 2 |
| Admin | `frontend/src/AdminApp.jsx` | 規格編輯表單加「2 粒裝」勾選框（讀寫 `is_two_pack`） |
| Seed | `backend/app/cli.py` | 「2 粒精緻禮盒」標 `is_two_pack=True` |

**後端下單防呆（server-side）**

- `backend/app/services/order_service.py` 建單流程：檢查每個 spec，若 `spec.is_two_pack` 且 `qty` 為奇數 → 拋 `EvenQtyRequiredError`。
- 新錯誤：`backend/app/core/exceptions.py` 加 `EvenQtyRequiredError`；`backend/app/api/errors.py` 對應碼 `EVEN_QTY_REQUIRED`（HTTP 422 或既有錯誤慣例）。
- 前端 `Cart.jsx` `formatApiError` 加 `EVEN_QTY_REQUIRED` → 「2 粒裝商品請以雙數（2、4、6…）購買」。

### B. 運費自動計算

| 檔案 | 變更 |
|------|------|
| `backend/app/core/constants.py` | `FREE_SHIPPING_THRESHOLD` 5000 → 3000；新增 `SHIPPING_BY_LAYER = {1: 130, 2: 150, 3: 180}` |
| `backend/app/services/order_service.py` | `compute_amounts` 改吃 items（含 `is_two_pack` 與 `qty`）：算 `layers = 非2粒箱數 + 2粒箱數//2`；`shipping = 0 if subtotal >= 3000 else SHIPPING_BY_LAYER[min(max(layers,1), 3)]`；`total = subtotal + shipping`。既有 `locked = [(spec, qty), ...]` 可直接算層數 |
| `frontend/src/Cart.jsx` | 同公式：由 `items`（`item.isTwoPack`, `item.count`）算層數與運費；`FREE_SHIPPING` 常數 5000 → 3000；`expected_total = subtotal + shipping`；免運進度條門檻改 3000 |

層數 helper 建議抽成純函式（前後端各一份、邏輯一致），方便測試。

### C. 運費／免運說明文字

- 文字：「運費：一層 $130 / 二層 $150 / 三層 $180」與「同住址滿 $3000 免運」。
- 位置一：購物車 footer / 結帳 order card 附近（`frontend/src/Cart.jsx`）。
- 位置二：storefront Notices 區（`frontend/src/Sections.jsx` 的 `Notices`）。

## 測試

- **後端單元**：`compute_amounts` 層數與運費（純非2粒、純2粒雙數、混合、達免運門檻、>3層 fallback）。
- **後端下單**：2 粒裝奇數 qty → `EVEN_QTY_REQUIRED`；雙數通過。
- **前端**：SpecCard 2 粒裝 ±2 行為；Cart 運費顯示與免運進度條；`expected_total` 與後端一致（避免 `PRICE_CHANGED`）。
- 既有 `backend/tests/test_order_service.py`、`test_schemas_order.py`、`test_products_api.py` 需更新以涵蓋新欄位與運費公式。

## 風險與注意

- **前後端運費必須完全一致**，否則 `expected_total` 對不上 → `PRICE_CHANGED` 擋單。層數公式共用同一份定義。
- Migration 用 `server_default='0'` 保護既有資料。
- 2 粒裝雙數在前端 UI 已約束，但後端仍須防呆（直接打 API 的情況）。
- Admin 勾選框寫入既有 spec CRUD，注意 `SpecUpdate` 部分更新語意（`None` = 不改）。

## 不做（YAGNI）

- 不重建 16A–40A 完整規格目錄（本次僅規則，規格資料另議）。
- 不處理 >3 層的多箱累加運費（產品組合不會在未免運下超過 3 層）。
