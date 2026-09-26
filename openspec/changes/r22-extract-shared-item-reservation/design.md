## Context

兩條路徑的差異只有：前台要比對 `expected_total`（在扣庫存前）、後台要先回補舊品項。其餘步驟相同。

## Goals / Non-Goals

**Goals:** 單一實作；行為與重構前完全相同（由既有測試加上本 change 的情境測試保證）。

**Non-Goals:** 不改變任何錯誤碼或回應形狀。

## Decisions

- **拆成兩階段 API**：`lock_and_validate(session, items) -> list[(spec, qty)]`（鎖定＋驗證，不扣庫存），與 `commit_reservation(locked) -> list[OrderItem]`（驗庫存、扣庫存、快照）。前台在兩者之間插入 `expected_total` 比對；後台在前面先 `release_items`。替代方案「單一函式加 callback」較難讀。
- 函式放在 `order_service`（前台服務），`admin_order_service` 相依它；這是既有的相依方向（已 import `order_service.compute_amounts`）。

## Risks / Trade-offs

- [重構引入行為差異] → 先補齊情境測試（紅燈階段可能已是綠燈，這是刻意的「特性測試」），再重構，重構前後全數通過。
