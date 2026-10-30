## Context

訂單品項保存商品名稱、規格名稱、下單價、數量與行小計，但沒有包裝類型。`apply_items` 計算金額時逐行讀規格現況，規格已刪除就落回箱裝；前端 `linesFromOrderItems` 為了與後端一致，同樣用規格清單判斷。`order_items.spec_id` 沒有 FK，規格硬刪除後舊 id 仍留著但查不到。下架（`is_active=False`）規格仍在，不受影響。

規格的包裝類型實際上可被 PATCH 改動（admin-catalog 有「變更包裝類型」情境），雖然 GLOSSARY 寫建立後不變；因此快照同時解決「刪除」與「改動」兩條路徑。

## Goals / Non-Goals

**Goals:**

- 既有訂單品項的層數在規格刪除或改動後維持下單時的結果。
- 後端與後台試算讀同一份快照，避免 `PRICE_CHANGED` 假警報。
- 既有資料一次回填完成，新程式不需處理 NULL。

**Non-Goals:**

- 不修正已被舊邏輯寫錯的歷史訂單金額；回填只補欄位，不重算 `shipping_fee` 或 `total`。
- 不改變「規格已刪除的訂單品項數量鎖定」規則。
- 不解決 GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改包裝類型之間的落差。
- 不處理 `spec_id` 為 NULL 的訂單品項在 `apply_items` 中的行為。
- 不新增 FK、不改規格硬刪除流程。

## Decisions

**D1. 欄位為 `order_items.is_two_pack: bool`，NOT NULL、`server_default=false`。** 沿用 `product_specs.is_two_pack` 的命名與型別。保留 server default 是因為 migration 先於新版程式跑，舊版程式在這段時間寫入的列不帶此欄位。替代方案「nullable，NULL 時回頭讀規格」會讓舊邏輯永遠留著，否決。

**D2. Migration 用單一 `UPDATE ... FROM product_specs` 回填。** 有規格者取規格值，其餘維持 server default 的 false。已下架規格仍在，自然被涵蓋。migration 的 `down_revision` 於實作時以 `alembic heads` 為準。

**D3. `apply_items` 的包裝類型來源集中成一個 helper。** 比照 `_unit_price`，新增 `_is_two_pack(current_by_spec, active, spec_id)`：既有行取 `existing.is_two_pack`，新增行取 `active[spec_id].is_two_pack`。步驟 5 不再需要為未變動的規格查 `spec_repo.get_by_id`，順帶減少查詢。新增行一定在 `active` 中，因為它不在 `current_by_spec` 就必然是數量變動且通過上架檢查。

**D4. 雙數檢查也改用同一個 helper（超出 ticket 字面範圍）。** ticket 只要求金額計算改用快照；但若雙數檢查仍讀規格現況，前端依快照放行、後端依規格拒絕，同一訂單品項會有兩種包裝類型。統一成「訂單品項一旦成立，它的包裝類型就是快照」。這個分歧只在規格被改包裝類型時才出現，影響面小。

**D5. `OrderItemRead.is_two_pack` 為必填，不給預設值。** 兩個組裝點（`order_service`、`admin_order_service`）都要明確傳入，漏傳時由 Pydantic 直接報錯。

**D6. `linesFromOrderItems` 的 `isTwoPack` 改讀 `it.is_two_pack`。** `specs` 參數保留，仍用於判斷 `locked`。`lineForSpec` 因此自動沿用快照。

## Testing Decisions

Seam 選最高層、且已有 prior art 的入口，不新增 seam：

- **HTTP API**（`tests/test_admin_orders_api.py`，`PATCH` 訂單）：主要回歸測試。建兩粒裝訂單品項，走 `DELETE /api/admin/specs/{id}` 真實硬刪除，再改同訂單其他訂單品項，斷言 `shipping_fee` 與 `is_two_pack`。同檔驗證後台回應、規格改包裝類型與加訂。
- **HTTP API**（`tests/test_orders_api.py`、`tests/test_admin_create_order_api.py`）：顧客下單與代客下單的快照及回應欄位。
- **Service against test DB**（`tests/test_order_items.py`）：`apply_items` 的快照優先順序與雙數檢查分支，用於 API 層不易湊出的組合。
- **Pure function**（`frontend/src/orderEdit.test.js`）：`linesFromOrderItems` 已刪除規格仍保留兩粒裝、總額試算一致。沿用現有 fixture 並補 `is_two_pack`。
- **Migration**：`tests/conftest.py` 以 `create_all` 建表，測試不經 Alembic，repo 也無 migration 測試的 prior art。回填以手動驗證：在本機 DB 準備規格仍在、已下架、已刪除三種列後跑 `alembic upgrade head`，再 `downgrade -1`、`upgrade head` 確認可逆。`compute_layers`／`compute_amounts` 介面不變，既有 `tests/test_order_amounts.py` 維持原樣。

## Risks / Trade-offs

- [舊版程式在 migration 後、新版上線前寫入的訂單品項為 false] → migration 跑完立刻部署新版後端，把空窗壓到最短；部署後檢查空窗內新建的訂單品項，必要時只對這些列補值。
- [前端先上線時 `is_two_pack` 為 undefined，兩粒裝被當箱裝] → 後端先部署，再部署前端。
- [回填用的是規格現況，若規格在下單後已改包裝類型，快照不是下單當時的值] → 無法還原，接受。
- [與 #29 方案 A 同時加 migration 會讓 alembic `down_revision` 分叉] → 不同時進行；後合併者重取 `alembic heads`。
- [與 #45 同改訂單品項 module（#45 只改錯誤訊息用語）] → 小衝突，錯開合併即可。
