# 訂單品項 module + 代客下單 — 設計

日期：2026-10-23

相關：`GLOSSARY.md`、ADR 0003（金額以後端為準）、ADR 0004（下單價成立即固定）

## 背景與問題

1. **預留邏輯複製三份。** 「鎖規格 → 上架檢查 → 兩粒裝雙數 → 庫存 → 扣庫存 → 快照下單價 → 算金額」在 `order_service.create_order`（`order_service.py:100-179`）與 `admin_order_service._replace_items`（`admin_order_service.py:174-222`）各寫一份，取消訂單還庫存（`admin_order_service.py:162-167`）是第三份。規則改動須三處同步。
2. **後台編輯會改寫下單價。** 前端 `saveEdit`（`AdminApp.jsx:543-556`）永遠帶 `items`；後端 `_replace_items` 把全部訂單品項整份覆蓋、以規格目前價格重新快照。只改地址也會讓舊訂單金額變動，違反 ADR 0004。
3. **已下架規格擋住整筆編輯。** `_replace_items` 對訂單內已下架規格丟 `NotFoundError`，導致含已下架規格的訂單連地址都改不了。
4. **後台無法代客下單。** 轉換期仍有電話訂購，目前只能請顧客自己上商店頁下單，無法把所有訂單統一在後台管理。

## 目標

1. 新增「訂單品項 module」：所有會建立或改動訂單品項的操作（顧客下單、代客下單、後台編輯、取消訂單）都經由它的一個 interface，規則只寫一處。
2. 後台編輯遵守 ADR 0004：既有訂單品項的下單價不變；只改顧客/收件資訊時訂單品項、金額、庫存完全不動。
3. 後台可完整管理訂單：代客下單、加訂、改數量、移除訂單品項、取消訂單。
4. 訂單記錄訂單來源，代客下單不觸發新訂單提醒。

## 非目標

- 店家規則單一來源（運費/免運/匯款資訊前後端各一份）——另立文件。
- `api.js` 加深、新訂單提醒 module 化——另立文件。
- 不提供實體刪除訂單；「刪除」即取消訂單。
- 不提供手動調整運費或折扣；運費一律照規則。
- 不做編輯歷史/稽核紀錄。
- 代客下單、後台編輯皆不發 LINE 通知。

## 業務規則

以下用語皆依 `GLOSSARY.md`。

### 訂單品項

- R1 同一訂單中每個規格至多一個訂單品項。請求內出現重複規格即拒絕。
- R2 訂單至少保留一個訂單品項；全部不要須改走取消訂單。
- R3 兩粒裝規格的數量須為雙數。
- R4 庫存不足即拒絕，整個操作不生效（同一 transaction）。

### 下單價

- R5 新成立的訂單品項（顧客下單、代客下單、加訂新規格）以當下規格價格作為下單價。
- R6 既有訂單品項的下單價永不改寫，包括數量改變時（整行沿用原下單價）。
- R7 金額（小計、運費、總額）一律由訂單品項的下單價與數量計算；運費依層數與免運門檻照規則。

### 後台編輯（僅待付款、待出貨）

- R8 可新增訂單品項：只能選**上架中且有庫存**、且不在此訂單中的規格。
- R9 可改上架中規格的訂單品項數量，庫存依差額扣除或補回。
- R10 已下架規格的訂單品項：保留，**數量不可改**，只能整行移除。
- R11 可移除任一訂單品項（含已下架），庫存補回。
- R12 既有訂單品項不能換規格；要換就移除再新增（新行適用 R5、R8）。
- R13 只改顧客/收件資訊時不送 `items`，訂單品項、金額、庫存不動，也不做金額比對。
- R14 已出貨、已取消的訂單不可編輯（維持現行；轉帳資訊仍可填）。

### 金額比對（ADR 0003）

- R15 顧客下單、代客下單、以及任何會改動訂單品項的後台編輯，送出時都帶 `expected_total`（畫面顯示的總額）。後端計算結果不一致即回 409 `PRICE_CHANGED`，附新金額明細，不寫入任何變更。

### 取消訂單

- R16 取消訂單（待付款/待出貨 → 已取消）補回所有訂單品項的庫存，包括已下架規格。

### 代客下單

- R17 規則與顧客下單相同（R1–R5、R7、R15），初始狀態待付款，付款方式轉帳。
- R18 無 LINE 身份欄位，不發 LINE 通知。
- R19 訂單來源記為代客下單；不觸發後台新訂單提醒（鈴聲、未讀數、新訂單橫幅）。

## 訂單品項 module

新檔 `backend/app/services/order_items.py`。這是本次的核心：所有呼叫端只認識下面兩個函式。

```python
class ItemRequest(NamedTuple):
    spec_id: int
    qty: int

class ItemsResult(NamedTuple):
    items: list[OrderItem]   # 新的完整訂單品項清單(既有的沿用原物件)
    amounts: Amounts

async def apply_items(
    session: AsyncSession,
    current: Sequence[OrderItem],      # 新訂單傳 []
    requested: Sequence[ItemRequest],  # 期望的完整訂單品項清單
    *,
    expected_total: int,
) -> ItemsResult: ...

async def release_items(session: AsyncSession, items: Sequence[OrderItem]) -> None: ...
```

### `apply_items` 的行為

以「期望的完整清單」對照「目前清單」，依規格比對出每一行的變化：

| 情況 | 處理 |
|---|---|
| 請求內規格重複 | `DuplicateSpecError`（R1） |
| 請求為空 | `ValueError`／schema 先擋（R2） |
| 規格只在 `current` | 移除：庫存補回（R11） |
| 規格只在 `requested` | 新增：須存在、上架中，否則 `NotFoundError`；下單價 = 規格目前價格（R5、R8） |
| 兩邊都有、數量相同 | 不動，不鎖規格、不碰庫存 |
| 兩邊都有、數量不同、規格上架中 | 庫存依差額調整，沿用原下單價（R6、R9） |
| 兩邊都有、數量不同、規格已下架 | `ItemQtyLockedError`（R10） |

接著依序：

1. 所有需異動庫存的規格以 `spec_repo.get_for_update` 鎖定（依 `spec_id` 排序鎖定，避免死結）。
2. 對有變動的行檢查兩粒裝雙數（R3）。
3. 先套用補回、再檢查扣除後庫存不為負；不足丟 `InsufficientStockError`（R4）。
4. 以全部訂單品項的下單價計算 `Amounts`（R7），與 `expected_total` 比對，不符丟 `PriceChangedError`（R15）。
5. 檢查都通過才實際寫入庫存與訂單品項。函式不 commit，由呼叫端 commit。

金額計算沿用 `order_service.compute_amounts`（之後可搬進此 module，非本次必要）。

### `release_items`

鎖定並補回每個訂單品項的庫存；規格不存在（已刪除）則略過。供取消訂單使用（R16）。

### 新增例外（`app/core/exceptions.py`）

- `ItemQtyLockedError`：`code = "ITEM_QTY_LOCKED"`，409，訊息「{規格} 已下架，數量不可修改」。
- `DuplicateSpecError`：`code = "DUPLICATE_SPEC"`，422。

## 呼叫端改動

| 呼叫端 | 改為 |
|---|---|
| `order_service.create_order` | `apply_items(session, [], items, expected_total=...)`；其餘（建 Order、LINE 通知）不變 |
| `admin_order_service.update_order` | `items` 有送才呼叫 `apply_items(session, order.items, items, expected_total=...)`；刪除 `_replace_items` |
| `admin_order_service.change_order_status`（→ 已取消） | `release_items(session, order.items)` |
| 新增 `admin_order_service.create_order` | `apply_items(session, [], items, expected_total=...)`，`source="admin"`，不發 LINE |

## 資料模型

`orders` 新增欄位（migration，`down_revision` 為實作時 `alembic heads` 的結果）：

- `source: str`，非 null，`server_default="storefront"`；值為 `storefront`（顧客下單）或 `admin`（代客下單）。既有訂單全部視為 `storefront`。

`app/models/order.py` 同步加 `source: Mapped[str]`。

## API

### `POST /api/admin/orders`（新）

代客下單。Body `AdminOrderCreate`（`extra="forbid"`）：

```python
class AdminOrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_name: str
    customer_phone: str
    customer_email: str | None = None
    shipping: ShippingCreate
    items: list[OrderItemCreate] = Field(min_length=1)
    note: str | None = None
    expected_total: int = Field(ge=0)
```

回應 201 `AdminOrderRead`。錯誤：`NOT_FOUND`、`DUPLICATE_SPEC`、`EVEN_QTY_REQUIRED`、`INSUFFICIENT_STOCK`、`PRICE_CHANGED`。

### `PATCH /api/admin/orders/{order_no}`（改）

`AdminOrderUpdate` 新增 `expected_total: int | None = None`；model validator：`items` 有送時 `expected_total` 必填。`items` 的語意改為「期望的完整訂單品項清單」，由 `apply_items` 依規格比對差異，不再整份覆蓋。

### 讀取

`AdminOrderRead`、`AdminOrderListItem` 新增 `source`。`GET /api/admin/orders` 新增選填查詢參數 `source`。

## 前端（`frontend/src`）

### 訂單編輯（`AdminApp.jsx` OrderModal）

- 既有訂單品項：規格顯示為文字，不再是下拉選單（R12）；顯示下單價。
- 數量欄：上架中規格可改（兩粒裝步進 2）；已下架規格停用並標示「已下架，數量不可修改」（R10）。
- 每行有移除按鈕；只剩一行時停用並提示「全部不要請取消訂單」（R2）。
- 「新增訂單品項」選單只列上架中、有庫存、且不在此訂單的規格（R8）；新行顯示目前價格。
- 即時試算總額：既有行用下單價、新行用目前價格，運費用 `pricing.js` 的 `computeShipping`/`computeLayers`。
- 送出時比對：訂單品項（規格+數量）與開啟時相同就不送 `items`（R13）；不同則送完整清單與 `expected_total`。
- 存檔前顧客/收件欄位走與商店頁、代客下單相同的 `validateCustomerShipping`（必填欄位不可為空或 null、電話格式）；希望送達日維持訂單原值時不受「不得早於明天」限制，改成新日期才檢查。
- 處理 409 `PRICE_CHANGED`（顯示新金額請重新確認）、`ITEM_QTY_LOCKED`、`INSUFFICIENT_STOCK`、`EVEN_QTY_REQUIRED`、`DUPLICATE_SPEC` 的錯誤訊息。

### 代客下單

- 訂單分頁新增「新增訂單」按鈕，開啟與編輯共用欄位的表單：顧客姓名、電話、Email（選填）、收件地址、希望到貨日、時段、備註、訂單品項。
- 規格選單規則同 R8；即時試算總額；送出帶 `expected_total`。
- 顧客/收件欄位驗證與商店頁購物車完全相同，兩邊呼叫同一個函式（`customerValidation.js` `validateCustomerShipping`）：姓名、電話（含格式）、縣市、區域、詳細地址必填，希望送達日不得早於明天；郵遞區號不必填。
- 送出按鈕與 `PRICE_CHANGED` 提示統一用「儲存訂單」。
- 成功後開啟該訂單明細並刷新列表。
- `api.js` 新增 `createAdminOrder(token, payload)`。

### 訂單來源顯示

- 訂單列表與明細顯示「代客下單」標籤（`source === 'admin'`）。
- 狀態篩選列旁新增訂單來源篩選（全部／顧客下單／代客下單）。

### 新訂單提醒（R19）

- `useOrderNotifications` 計算 `newestCreatedAt`、未讀與鈴聲時排除 `source === 'admin'` 的訂單。
- `AdminApp` 新訂單橫幅同樣排除。

## 測試

### 後端：`tests/test_order_items.py`（新，打 `apply_items`/`release_items` interface）

- 新訂單：快照目前價格、扣庫存、金額正確。
- 數量相同的既有行：不碰庫存、下單價不變。
- 規格調價後加量：整行沿用原下單價，只扣差額庫存。
- 減量：補回差額庫存。
- 加訂新規格：用目前價格。
- 移除行：補回庫存；含已下架規格。
- 已下架規格改數量 → `ITEM_QTY_LOCKED`，庫存不變。
- 已下架規格保留不動 → 成功（現行會 `NOT_FOUND`，此為回歸測試）。
- 新增已下架/不存在規格 → `NOT_FOUND`。
- 請求重複規格 → `DUPLICATE_SPEC`。
- 兩粒裝單數 → `EVEN_QTY_REQUIRED`。
- 庫存不足 → `INSUFFICIENT_STOCK`，且所有庫存不變。
- `expected_total` 不符 → `PRICE_CHANGED`，且庫存、訂單品項不變。
- `release_items` 補回全部庫存。

### 後端：既有測試調整

- `test_admin_order_service.py` / `test_admin_orders_api.py`：
  - 只改地址（不送 `items`）→ 金額、下單價、庫存不變。
  - 規格調價後只改地址 → 下單價不變（此 bug 的回歸測試）。
  - 送 `items` 未帶 `expected_total` → 422。
  - 代客下單：成功建立、`source == "admin"`、不呼叫 LINE、`PRICE_CHANGED` 擋下。
  - 列表 `source` 篩選。
- `test_order_service.py` / `test_orders_api.py`：顧客下單行為不變，`source == "storefront"`。

### 前端

- 抽出純函式 `orderItemsDiff(original, form)`（判斷是否需送 `items`）與 `previewAmounts(lines)`，以 vitest 測試。
- 新訂單提醒排除代客下單的邏輯放在 `notifications.js`，補測試。
- CI（`.github/workflows/ci.yml`）新增 `npm test --prefix frontend`，讓前端測試實際被執行。

## 部署

依 ADR 0002：合併進 master 後手動執行 migration job、部署後端、再部署前端。migration 只新增帶預設值的欄位，可先於新版後端上線。
