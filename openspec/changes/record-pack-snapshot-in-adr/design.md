## Context

#46（PR #78）讓訂單品項保存包裝類型，既有訂單品項的層數與雙數檢查改讀快照。`order-pricing` 與 `order-items` 已寫明這項行為，但 ADR 仍停在舊說法：

- ADR 0003：「後端以規格現況重新計算」。ADR 0004 起這句對既有訂單品項就不成立，#46 又多一個例外。
- ADR 0004：只固定下單價，沒提包裝類型。

本票只補文件，並為這條跨兩個欄位的金額基礎補一個情境。

## Goals / Non-Goals

**Goals:**

- 從 ADR 能讀到：既有訂單品項的金額基礎是下單價與包裝類型，兩者都在成立時固定。
- ADR 0003 與 0004 不互相矛盾。

**Non-Goals:**

- 改任何金額行為或 production 程式碼。
- GLOSSARY「包裝類型建立後不變」與 admin-catalog 可改包裝類型的落差：#84。ADR 用語採「規格改動或刪除」，不對規格能否改包裝類型表態。
- 錯誤訊息用語：#83。
- 運費規則前後端各寫一份的現況（ADR 0003 已記為代價）。

## Decisions

### D1. 就地修訂 ADR 0003、0004，不開新 ADR

包裝類型快照與下單價是同一個決策「成立後金額基礎固定」的延伸，分開寫要多讀一份才知道全貌，且 0003 的錯句仍得改。否決：新增 ADR 0006。

檔名不改，保留既有連結；ADR 0004 的標題可改。

### D2. ADR 目標內容

ADR 0003 第二句改為：

> 送出訂單時前端帶上 `expected_total`，後端重新計算：新的訂單品項讀規格現況，既有訂單品項讀成立時固定的下單價與包裝類型（見 ADR 0004）；兩者不一致就回 409（`PriceChangedError`）並附上新的金額明細，由顧客重新確認。

其餘句子不動。

ADR 0004 標題改為「訂單品項的下單價與包裝類型一經成立即固定，後台編輯不重新定價」，本文補：

- 包裝類型決定層數，層數決定運費，因此與下單價同樣在訂單品項成立時固定；之後規格改動或刪除都不影響既有訂單品項。
- 導入前只快照下單價，規格刪除後兩粒裝被當箱裝換算，只編輯同訂單的其他訂單品項就可能改寫運費。
- 雙數檢查同樣依快照判定；新增的訂單品項仍讀規格現況。

Considered Options 加一項：既有訂單品項的層數繼續讀規格現況，否決，理由為規格刪除或改動會改寫顧客已同意的運費。

### D3. Spec 改「金額以後端計算為準」

這條是 ADR 0003 對應的需求，金額基礎寫在這裡，ADR 與 spec 才對得上。既有「包裝類型以訂單品項快照判定」只談層數，不改。

## Testing Decisions

- 測試入口：HTTP API，後台修改訂單品項。下單價與包裝類型的組合只有走完整請求才看得到，且 `test_admin_orders_api.py` 已有同層測試，不另開 service 層測試。
- Prior art：`backend/tests/test_admin_orders_api.py` 的 `test_spec_pack_change_keeps_item_snapshot_and_layers`、`test_added_item_snapshots_current_pack_type`；`backend/tests/test_order_items.py` 的 `test_increase_after_price_change_keeps_unit_price_and_deducts_difference`。
- 行為已存在，新測試是 characterization test，預期一寫就通過，是本 repo TDD 規則的例外。它若失敗，代表 spec 與現況不符，停下回報，不改 production 程式碼。
- 其餘三個情境已由既有測試涵蓋，不新增：`test_create_order_price_changed_409`、`test_admin_create_order_price_changed_409_writes_nothing`、`test_update_order_items_price_changed_writes_nothing`。

## Risks / Trade-offs

- [ADR 0004 改標題後與檔名不一致] → 保留檔名以免斷連結；檔名描述的下單價仍屬實。
