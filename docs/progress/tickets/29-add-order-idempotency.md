# #29 POST /api/orders 無冪等性，連點會建立重複訂單

- 狀態：完成
- OpenSpec change：`add-order-idempotency`（archive 後：`openspec/changes/archive/2026-10-30-add-order-idempotency/`）
- Branch：`claude/nostalgic-tesla-546ee8`
- 最後更新：2026-10-30

## 做了什麼
- 連點、逾時重試或 WebView 重送只成立一張訂單，重送拿到原訂單編號，不重複扣庫存、不重複發 LINE 通知。
- 商店頁送出時同步鎖住，同一輪事件內連按也只發一個請求。
- 內容未變的重試沿用 key；內容改變或訂單成立後換新 key。
- 未帶 `Idempotency-Key` 的請求行為不變，舊版前端不受影響。

## 決定與偏離
- 依 [design.md](../../../openspec/changes/archive/2026-10-30-add-order-idempotency/design.md) D1–D10 實作，無偏離。
- `down_revision` 取實作當下的 head `d3a91c7e5f20`（#46 已合併）。
- Review 後補記 design.md Risks：好友狀態重查範圍比原文廣；`Cart.jsx` 只保存最後一組 key。兩者都接受，未改 code。
- 部署順序：migration、後端、前端。

## 驗收結果
- [x] 下單冪等性 — 相同 key 重送：`test_same_key_returns_original_order_once`
- [x] 下單冪等性 — 重送不重複扣庫存：`test_same_key_returns_original_order_once`
- [x] 下單冪等性 — 原訂單成立後條件改變：`test_same_key_returns_original_order_after_price_or_stock_change`
- [x] 下單冪等性 — 相同 key 同時送達：`test_same_key_concurrent_creates_one_order`
- [x] 下單冪等性 — 相同 key 同時搶最後庫存：`test_same_key_concurrent_for_last_stock_creates_one_order`
- [x] 下單冪等性 — 失敗的請求不佔用 key：`test_rejected_request_does_not_consume_key`
- [x] 下單冪等性 — 不同 key：`test_different_keys_create_separate_orders`
- [x] 下單冪等性 — 未帶 key：`test_requests_without_key_create_separate_orders`
- [x] 下單冪等性 — 公開回應不含 key：`test_same_key_returns_original_order_once`
- [x] Idempotency-Key 格式驗證 — 空的 key：`test_invalid_key_length_422`
- [x] Idempotency-Key 格式驗證 — 過長的 key：`test_invalid_key_length_422`
- [x] 商店頁防重複送出 — 送出中再次點擊：手動，瀏覽器 stub 下單 API，按鈕為 disabled 且顯示「送出中...」
- [x] 商店頁防重複送出 — 連續快速點擊：手動，同一輪事件 `click()` 兩次，只發 1 個請求
- [x] 商店頁防重複送出 — 失敗後重試沿用 key：手動，stub 網路錯誤後重送，key 相同；`checkoutKey.test.js`
- [x] 商店頁防重複送出 — 改內容後換 key：手動，失敗後改備註再送，key 不同；`checkoutKey.test.js`
- [x] 商店頁防重複送出 — 訂單成立後再次結帳：手動，成立後以相同 body 再結帳，key 不同
- [x] 僅在訂單成立時通知 — 訂單狀態變更：既有行為未動，`line_service` 只由 `create_order` 成功路徑呼叫
- [x] 僅在訂單成立時通知 — 重送回傳原訂單：`test_same_key_returns_original_order_once`、`test_same_key_concurrent_creates_one_order`

Migration 手動驗證：空 DB 上 `upgrade head`、`alembic check` 無差異、`downgrade -1` 欄位移除、再 `upgrade head` 欄位與唯一約束存在。

## 留待之後
- `Idempotency-Key` 長度上限只在 route，DB 欄位無長度限制（D2）。
- `Cart.jsx` 送單接線無自動化測試：前端無 jsdom／component 測試基礎。

## 下一步
- 無。

## Review
