## Context

`POST /api/orders` 不需登入。回應欄位由回應結構決定，現況已不含顧客個資、LINE 身份與轉帳資訊，但 `test_create_order_201` 只斷言回應內沒有 `stock_qty`。此缺口由 PR #77 的自動審查提出（#67 是前端重構，不處理）。

## Goals / Non-Goals

**Goals:**

- 有測試鎖住公開下單回應的欄位，回應新增欄位時測試失敗。
- 規格情境明列回應內容，能直接對照測試。

**Non-Goals:**

- 不改回應結構、API 行為或前端。
- 不處理 409 `PRICE_CHANGED` 等錯誤回應的內容。
- 不處理後台 API 的回應；後台欄位本來就該出現在那裡。
- 不改既有測試（`test_create_order_201` 的 `stock_qty` 斷言保留）。

## Decisions

**用完整欄位清單比對，不用黑名單。** ticket 建議斷言 `customer_name`、`customer_phone`、`line_user_id`、`transfer_last5` 等欄位不存在。黑名單只擋列出的名字，改名或新欄位（例如 `shipping`、`customer`）都會漏掉；比對完整 key 集合會擋下任何新欄位，也涵蓋黑名單的所有項目。代價是之後要合法擴充回應時得一起改測試，但這正是要的審視點。

**頂層與訂單品項都要比對。** 訂單品項是巢狀結構，只比對頂層會漏掉品項裡多出的欄位。

**請求帶齊顧客個資與 LINE 身份。** 既有 `_body` 已帶這些資料，讓測試在「有資料可洩漏」的條件下跑，不是空值時才通過。

## Testing Decisions

- **入口**：HTTP API（`POST /api/orders`，透過 `client` fixture），是最高的現有 seam，也是洩漏實際發生的地方；不測 schema 類別本身。
- **位置**：`backend/tests/test_orders_api.py`，新增獨立測試 `test_create_order_response_excludes_admin_fields`，重用該檔的 `_seed_spec`、`_body`。
- **Prior art**：同檔 `test_create_order_201`。
- **因為行為已存在**，新測試一開始就會通過。tasks 以暫時把欄位加進回應的方式確認它會失敗，驗證測試真的有效，確認後還原。

## Risks / Trade-offs

- 與 #57（`add-shared-test-factories`）同改 `test_orders_api.py`：#57 會把規格 seed 改用工廠。本票只新增測試、呼叫 `_seed_spec`，後合併者依當時 helper 調整一行即可，不需阻擋關係。
