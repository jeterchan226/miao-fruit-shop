## Context

`OrderSource` 是 `core/constants.py` 的 `Literal`，後台列表的 route、service、repository 都用它，無效值由 FastAPI 回 422。同一組參數的 `status` 三層都是 `str`，有效值另外寫在 `OrderStatusUpdate.status` 的 `Literal` 與 `VALID_TRANSITIONS` 的 key。

`openspec/specs/admin-orders/spec.md` 有「訂單狀態篩選值不驗證」：無效值回 200 與空列表。這條來自 baseline（`cd552c7`，由現有行為補寫），沒有 ADR，也沒有測試固定它。

前端 `FilterStrip` 只送四種訂單狀態，「全部」是空字串，`listAdminOrders` 會略過空值，所以後台介面不會碰到 422。

## Goals / Non-Goals

**Goals:**

- `status` 參數從 route 到 repository 使用同一個有限值型別，與 `source` 一致。
- 訂單狀態的有效值只定義一次。
- 無效的篩選值回 422，OpenAPI 顯示 enum。

**Non-Goals:**

- 不改 `Order.status`（維持 `Mapped[str]`）、不加 DB CHECK constraint、不做 migration。
- 不改回應欄位 `AdminOrderListItem.status`、`AdminOrderRead.status`、`AdminOrderSummary` 與 `count_by_status` 的型別。
- 不改 `VALID_TRANSITIONS`、`NOT_EDITABLE_STATUSES`，也不新增 `ORDER_STATUS_*` 常數。
- 不改前端。
- 不改「訂單列表篩選」這條 requirement 的內容。

## Decisions

### 新增 `OrderStatus`，與 `OrderSource` 同一寫法

在 `core/constants.py` 宣告 `OrderStatus = Literal["pending_payment", "ready", "shipping", "cancelled"]`，順序同 `VALID_TRANSITIONS`。`OrderStatusUpdate.status` 改用它，有效值只留一份。`Final` 常數沒有使用者，不加。

### route 也改型別，無效值回 422

只改 repository 與 service 時，route 傳下來的 `str` 過不了 `mypy` strict；用 `cast` 會讓型別宣稱一件沒驗證過的事。route 用 `OrderStatus | None`，型別才是真的，代價是行為改變：無效值由 200 改為 422。

這與 #92 要的「和 `source` 一致」同一方向，而 `source` 在 route 就是 `Literal`。「不驗證」只是 baseline 記下的現狀，不是決定過的規則，後台介面也不受影響，所以直接改，並在 PR 標出這個行為變更。

### 空字串視為無效

`?status=` 由 FastAPI 依 `Literal` 回 422，與 `source` 相同。不加轉換：唯一的呼叫端不會送空字串。

### 以 REMOVED + ADDED 改 spec，不動「訂單列表篩選」

#43、#91 的 delta 都整段 MODIFIED「訂單列表篩選」。#92 若也改它，就要排在它們之後，否則後封存的一方會蓋掉別人的 scenario。獨立成一條 requirement 後不需排序，因此 #92 不加 `Blocked by`。

`list_filtered` 的 `status` 參數列不在 PR #89 的改動範圍內，程式碼只有 import 附近可能需要簡單合併。

## Testing Decisions

測試入口是 HTTP API（最高的現成 seam），加在 `backend/tests/test_admin_orders_api.py`，用現有 `client` fixture：

| Scenario | 測試 |
|---|---|
| 依訂單狀態篩選 | 參數化四種狀態，擴充 `test_list_orders_filter_by_status` |
| 無效的訂單狀態 | 新增，比照 `test_list_orders_invalid_source_422` |
| 空的訂單狀態 | 同上，`?status=` |
| 未帶訂單狀態 | 既有無篩選測試涵蓋，不新增 |
| 參數宣告為 enum | 新增，讀 `GET /openapi.json`，比對 `/api/admin/orders` 的 `status` 參數 enum，預期值用 `get_args(OrderStatus)` |

`backend/tests/test_constants.py` 另外固定 `get_args(OrderStatus)` 的四個值與順序，比照 `OrderSource`。型別一致性由 `mypy app` 驗證，不另寫測試。

參考前例：`spec/type-admin-order-source`（#66）的 OpenAPI 斷言寫法。

## Risks / Trade-offs

- 外部呼叫端依賴 200 空列表 → repo 內唯一呼叫端是後台介面，且只送有效值；此 API 需管理員身分，沒有其他已知使用者。
- 部署順序 → 新舊前端都不送無效值，後端可獨立部署。
- `get_args(OrderStatus)` 與 `VALID_TRANSITIONS` 的 key 重複 → 本次不統一，範圍外。
