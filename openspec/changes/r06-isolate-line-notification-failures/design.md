## Context

`send_order_created` 以 `asyncio.to_thread` 執行同步的 LINE SDK。它在 service 內被 await，所以 LINE 的延遲與錯誤都會反映到下單回應。

## Goals / Non-Goals

**Goals:** 下單成功與否只取決於資料庫交易；推播為 best-effort。

**Non-Goals:** 不做推播重試佇列（Cloud Tasks / Pub/Sub）；不做「推播失敗」後台提示。

## Decisions

- **`BackgroundTasks`，而非 `asyncio.create_task`**：`BackgroundTasks` 由 Starlette 管理，在回應後執行且測試中 `TestClient`/`httpx` 會等待完成，便於斷言；`create_task` 可能在 Cloud Run 請求結束、CPU 被節流後遺失。
- 背景任務只需要 `order_no` 等純資料，**不傳 ORM 物件**（session 已關閉）。在 service 內 commit 後把組 Flex 所需的欄位轉成不可變的 `OrderNotification` dataclass 傳給背景任務。
- service 介面改為回傳 `(OrderRead, OrderNotification | None)`，由 route 決定是否排入背景任務，service 本身不依賴 FastAPI。

## Risks / Trade-offs

- [Cloud Run 預設「僅在請求期間配置 CPU」，回應後的背景任務可能被節流] → `BackgroundTasks` 在同一個 ASGI 請求週期內執行（回應 body 送完後、請求結束前），Cloud Run 仍視為請求期間；在 design 驗證時以正式環境實測一次。
- [捕捉 `Exception` 可能掩蓋 bug] → 一律 `logger.exception` 並附 `order_no`，可由 Cloud Logging 告警。
