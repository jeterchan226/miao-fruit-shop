## 1. 相同 key 只成立一張訂單

- [x] 1.1 寫失敗 API 測試：相同 key 送兩次皆 201、`order_no` 相同、訂單一筆、庫存只扣一次、LINE 只發一次；回應不含 `idempotency_key`
- [x] 1.2 寫失敗 model 測試：相同 key 第二筆寫入被拒，多筆 NULL 可共存
- [x] 1.3 `Order` 新增 nullable、unique 的 `idempotency_key`
- [x] 1.4 新增 Alembic migration；`down_revision` 取實作當下 `alembic heads`（注意 PR #78 的 `d3a91c7e5f20`），確認只有一個 head
- [x] 1.5 `order_repo` 新增 `get_by_idempotency_key`
- [x] 1.6 `place_order` 接受 `idempotency_key`；`create_order` 先查，命中回原訂單且不發通知
- [x] 1.7 route 讀取選填 `Idempotency-Key` header（長度 1–128）並傳給 service

## 2. 邊界行為

- [x] 2.1 寫 API 測試：訂單成立後調價或售完，重送回原訂單
- [x] 2.2 寫 API 測試：`PRICE_CHANGED` 被拒的 key 之後可成立訂單
- [x] 2.3 寫 API 測試：不同 key、未帶 key 各成立兩張；空字串與超過 128 字元回 422 且不成立訂單
- [x] 2.4 補齊讓上述測試通過所需的實作

## 3. 同時送達

- [x] 3.1 寫失敗並發測試（兩個 committing session + `asyncio.gather`，含逾時）：相同 key 同時送達，一張訂單、庫存扣一次、`order_no` 相同
- [x] 3.2 寫失敗並發測試：庫存只夠一張時相同 key 同時送達，兩個請求皆拿到同一張訂單
- [x] 3.3 `create_order` 接 `IntegrityError` 與 `AppError`：rollback 後再查，查到回原訂單，查不到重新拋出

## 4. 前端 key 與送出

- [x] 4.1 寫失敗測試：`nextCheckoutKey` 內容相同沿用、內容不同換新；無 `crypto.randomUUID` 時以 `getRandomValues` 產生合法 v4 UUID
- [x] 4.2 新增 `checkoutKey.js`
- [x] 4.3 寫失敗測試：`createOrder` 帶 `Idempotency-Key` header
- [x] 4.4 `createOrder` 接受 key 並送出 header
- [x] 4.5 `Cart.jsx` 以 ref 保存 key，送單時取 `nextCheckoutKey`，訂單成立後清空
- [x] 4.6 `Cart.jsx` 送出加同步 ref 鎖，請求結束解鎖

## 5. 驗證

- [x] 5.1 手動驗證 migration：`upgrade head`、`downgrade -1`、`upgrade head`
- [x] 5.2 手動驗證前端：連按送出只發一個請求；模擬失敗後未改內容重送沿用 key，改內容換 key；成立後再次結帳換 key
- [x] 5.3 `uv run ruff check .`、`uv run mypy app`、`uv run pytest -q` 全過
- [x] 5.4 `npm run test`、`npm run build` 全過
