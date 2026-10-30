# #83 訂單品項錯誤訊息改用快照名稱與正確用語

- 狀態：完成
- OpenSpec change：`correct-order-item-error-messages`（archive 後：`openspec/changes/archive/2026-10-30-correct-order-item-error-messages/`）
- Branch：`claude/amazing-sanderson-bc888d`
- 最後更新：2026-10-31

## 做了什麼
- 既有訂單品項的雙數限制與庫存不足訊息改用快照名稱；新增的訂單品項維持規格現況名稱。
- 後台 `PRICE_CHANGED` 提示改為「規格價格或包裝類型已更新」，後台編輯訂單與代客下單共用。

## 決定與偏離
- 無偏離。決定見 [design.md](../../../openspec/changes/archive/2026-10-30-correct-order-item-error-messages/design.md)。
- 「2 粒裝」訊息用語刻意未改，屬 #45 範圍；後合併者須同時保留快照名稱與「兩粒裝」。
- Code review 指出 `_spec_label` 與 `_unit_price`、`_is_two_pack` 形狀重複：未抽象，design.md 明定與它們一致。

## 驗收結果
- [x] 錯誤訊息以訂單上的名稱稱呼訂單品項 — 雙數限制訊息用快照名稱：`test_even_qty_message_uses_snapshot_label_for_existing_item`
- [x] 錯誤訊息以訂單上的名稱稱呼訂單品項 — 庫存不足訊息用快照名稱：`test_insufficient_stock_message_uses_snapshot_label_for_existing_item`
- [x] 錯誤訊息以訂單上的名稱稱呼訂單品項 — 新增的訂單品項用規格現況名稱：`test_error_messages_use_current_label_for_new_item`
- [x] 後台編輯訂單介面 — 僅剩一個訂單品項：本 PR 未動。此 scenario 無自動測試（`validateLines([])` 只測零行，非此狀態）；手動讀 `OrderItemsEditor.jsx:16,95-96,104` 確認
- [x] 後台編輯訂單介面 — 已下架規格的訂單品項：本 PR 未動。`已下架規格的行鎖定數量(R10)`；欄位停用與標示無自動測試，手動讀 `OrderItemsEditor.jsx:56-57,78,85` 確認
- [x] 後台編輯訂單介面 — 價格已更新：本 PR 只改提示字串，判定與試算未動。訊息：`PRICE_CHANGED 顯示新金額請重新確認`；重新試算：`repriceNewLines` 測試組；`AdminApp.jsx` 串接兩者的流程無自動測試，手動讀 `AdminApp.jsx:739-745,1042-1048` 確認
- [x] 後台編輯訂單介面 — 提示涵蓋包裝類型改動：`orderEdit.test.js`「PRICE_CHANGED 顯示新金額請重新確認」
- [x] 後台編輯訂單介面 — 保留過去的送達日：本 PR 未動。驗證規則：`送達日維持原值即使已過 → 放行;改成早於明天的新日期 → 擋下`；實際儲存流程無自動測試

## 留待之後
- GLOSSARY「規格名稱建立後不變」與規格更新 API 可改 `label` 的落差：#98。
- 雙數限制訊息的「2 粒裝」用語：#45；後合併者須同時保留快照名稱與「兩粒裝」。

## 下一步
- 無。

## Review
