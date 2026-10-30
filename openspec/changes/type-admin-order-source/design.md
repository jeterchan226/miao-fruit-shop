## Context

訂單來源型別 `OrderSource` 是 `Literal["storefront", "admin"]`。route 查詢參數、service、repository 都已使用，只有 `AdminOrderListItem.source`、`AdminOrderRead.source` 還是 `str`。`Order.source` 是 `Mapped[str]`，資料庫欄位為字串，無 CHECK constraint。

寫入訂單來源的路徑只有兩條：顧客下單與代客下單，都帶常數；欄位 server default 為 `storefront`。

## Goals / Non-Goals

**Goals:**

- 兩個回應欄位改用 `OrderSource`，OpenAPI 顯示 enum。
- 用測試固定 OpenAPI 契約，防止回應型別退回 `str`。

**Non-Goals:**

- 不改 `Order.source` 的型別（理由見 Decisions）。
- 不加 DB CHECK constraint、不做 migration。
- 不改 `OrderRead`（顧客下單回應本來就沒有 `source`）與其他字串欄位（`status`、`payment_method`）。
- 不改前端：JSON 內容不變。

## Decisions

### 回應欄位直接宣告 `OrderSource`

兩個欄位改為 `source: OrderSource`。FastAPI 會由 Literal 產生 enum；以暫時改動實測，兩個 schema 的 OpenAPI 都輸出 `{"type": "string", "enum": ["storefront", "admin"]}`。

### `Order.source` 維持 `Mapped[str]`

這是 #66 留待開工決定的問題。維持不變，因為實測只改 schema 時 `mypy app` 已通過，model 不需要跟著改。改成 `Mapped[OrderSource]` 要另外指定 `String` 欄位型別，增加改動卻沒有換到執行期保障，型別宣告也擋不住資料庫裡的值。

### 不處理回應序列化失敗

既有訂單的來源若不在 enum 內，Pydantic 驗證失敗，查單 API 回 500，且列表中一筆壞資料會讓整頁失敗。不加容錯：程式碼沒有寫入其他值的路徑，容錯反而會藏住資料問題。改以部署前查一次正式資料把關。

## Testing Decisions

- 測試入口：HTTP API，以現有 `client` fixture 讀 `GET /openapi.json`，斷言 `AdminOrderListItem`、`AdminOrderRead` 的 `properties.source.enum` 為 `["storefront", "admin"]`。這是最高的現成 seam，也能驗到對外契約。
- 回應內容不變由既有測試涵蓋：`test_list_orders_items_include_source`、`test_get_order_detail`（`backend/tests/test_admin_orders_api.py`），不新增。
- 參考前例：同檔的 API 測試；`backend/tests/test_constants.py` 固定 `OrderSource` 的值，enum 的預期值可引用 `get_args(OrderSource)`。

## Risks / Trade-offs

- 正式資料有其他值時查單 API 回 500 → 部署前執行 `SELECT source, count(*) FROM orders GROUP BY source`，只有 `storefront`、`admin` 才部署；有其他值就先停止部署，回報使用者。
- 與 #48 同改 `backend/app/schemas/order.py` → 不同時進行。
- OpenAPI 輸出改變 → repo 內沒有由 OpenAPI 產生的 client，前端不受影響。
