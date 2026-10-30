## Context

訂單品項 module 的 `apply_items` 已對單價與包裝類型採「既有用快照、新增用規格現況」，已下架訊息也用 `spec_label`；但雙數限制與庫存不足訊息直接讀規格現況的 `label`。#83 點名雙數限制訊息，同一流程的庫存不足訊息是同一缺陷。

`orderEditErrorMessage` 由後台編輯訂單與代客下單共用。`PRICE_CHANGED` 在新增訂單品項的規格調價時發生，也在其包裝類型改動、層數與運費隨之改變時發生，所以「規格價格已更新」不完整。

## Goals / Non-Goals

**Goals:**

- 既有訂單品項的雙數限制與庫存不足訊息使用快照名稱。
- 後台 `PRICE_CHANGED` 提示涵蓋包裝類型改動。

**Non-Goals:**

- 「2 粒裝」改「兩粒裝」的用語調整：由 #45 處理。
- 商店頁「商品價格已更新」提示與後端 `PRICE_CHANGED` 的 `detail`：#83 未點名，後台也不顯示該 `detail`。
- 已下架訊息：已使用快照名稱。
- 錯誤代碼、API 形狀、判定規則；#84 的 GLOSSARY 落差。

## Decisions

- **庫存不足訊息一併修正**：與雙數限制訊息是同一缺陷、同一函式，只修一則會留下相同的不一致。
- **名稱取得方式與 `_unit_price`、`_is_two_pack` 一致**：以同樣的既有優先判定取名稱，不在訊息處各寫一次條件。
- **提示改為「規格價格或包裝類型已更新，新的訂單總額為 …，請重新確認後再儲存訂單。」**：說出兩種成因，比泛稱「規格已更新」更能指引管理員。其餘字句不動。
- **`order-items` 用 ADDED，不改「兩粒裝須以雙數購買」**：#45 已 MODIFIED 該 requirement，獨立成新 requirement 讓兩個 change 以任意順序封存都不互相覆蓋，因此 #83 不依賴 #45。
- **`admin-orders` 用 MODIFIED 並新增 scenario**：既有「價格已更新」scenario 仍成立。

## Testing Decisions

- **後端訊息：service against the test DB**。沿用 `apply_items` 這條最高的既有 seam，在 `backend/tests/test_order_items.py` 以 `_existing_order` 建立既有訂單品項後改 `spec.label`，用 `pytest.raises(...) as exc` 斷言 `exc.value.detail` 含快照名稱、不含現況名稱。新增的訂單品項同樣斷言含現況名稱。Prior art：`test_existing_two_pack_snapshot_rejects_odd_qty_after_spec_became_box`。
- **斷言用「含／不含名稱」，不比對完整字串**：完整字串會與 #45 的「兩粒裝」用語耦合，造成合併順序依賴。
- **HTTP 層不加測試**：訊息只經 exception handler 原樣傳遞，既有 API 測試已涵蓋 409 與代碼。
- **後台提示：純函式**。更新 `frontend/src/orderEdit.test.js` 的 `PRICE_CHANGED` 測試為新字串。Prior art：同一測試。

## Risks / Trade-offs

- 與 #45 同改雙數限制訊息同一行：後合併者手動合併，訊息須同時用快照名稱與「兩粒裝」。
- `detail` 文字改變：前端只顯示不比對，沒有外部依賴。
