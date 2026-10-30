# #46 訂單品項快照加入「是否兩粒裝」

- 狀態：完成
- OpenSpec change：`add-order-item-pack-snapshot`（archive 後：`openspec/changes/archive/2026-10-30-add-order-item-pack-snapshot/`）
- Branch：`claude/modest-chebyshev-27dc6d`
- 最後更新：2026-10-30

## 做了什麼
- 訂單品項成立時（顧客下單、代客下單、加訂新規格）保存包裝類型。
- 規格刪除或改包裝類型後編輯訂單，既有訂單品項的層數與雙數檢查維持快照，運費不再被改寫。
- 顧客與後台訂單回應的訂單品項帶出 `is_two_pack`；後台編輯試算改讀它。
- 既有訂單品項依規格回填，查無規格者為箱裝。

## 決定與偏離
- 雙數檢查也改採快照，見 [design.md](../../../openspec/changes/archive/2026-10-30-add-order-item-pack-snapshot/design.md) D4。
- 部署順序：migration 跑完立刻部署新版後端，再部署前端（design.md Risks）。

## 驗收結果
- [x] 既有訂單品項回填包裝類型 — 規格仍存在：手動，暫存 DB 上架、已下架兩粒裝列回填為 true，箱裝為 false
- [x] 既有訂單品項回填包裝類型 — 規格已刪除：手動，spec_id 查無與 NULL 的列皆為 false；`downgrade -1` 後再 `upgrade head` 結果相同
- [x] 訂單回應帶出包裝類型 — 後台訂單詳情：`test_order_detail_includes_pack_type`
- [x] 訂單回應帶出包裝類型 — 規格已刪除的訂單品項：`test_order_detail_keeps_pack_type_after_spec_deleted`
- [x] 兩粒裝須以雙數購買 — 奇數數量：`test_two_pack_odd_qty_rejected`
- [x] 兩粒裝須以雙數購買 — 雙數數量：`test_two_pack_even_qty_ok`
- [x] 兩粒裝須以雙數購買 — 既有訂單品項依快照判定：`test_box_snapshot_allows_odd_qty_after_spec_became_two_pack`、`test_existing_two_pack_snapshot_rejects_odd_qty_after_spec_became_box`
- [x] 下單價與名稱快照 — 成立後規格調價：`test_update_order_address_only_after_price_change_keeps_order_price`、`test_unchanged_item_keeps_unit_price_and_stock`
- [x] 下單價與名稱快照 — 成立時的快照：`test_new_order_snapshots_current_price_and_deducts_stock`、`test_create_order_snapshots_pack_type`
- [x] 下單價與名稱快照 — 代客下單的包裝類型快照：`test_admin_create_order_snapshots_pack_type`
- [x] 下單價與名稱快照 — 加訂新規格的包裝類型快照：`test_added_item_snapshots_current_pack_type`
- [x] 下單價與名稱快照 — 成立後規格改包裝類型：`test_spec_pack_change_keeps_item_snapshot_and_layers`
- [x] 包裝類型以訂單品項快照判定 — 兩粒裝規格已刪除後編輯訂單：`test_update_items_after_two_pack_spec_deleted_keeps_layers`
- [x] 包裝類型以訂單品項快照判定 — 規格的包裝類型被改動：`test_spec_pack_change_keeps_item_snapshot_and_layers`、`test_existing_item_layers_use_snapshot_not_current_spec`
- [x] 包裝類型以訂單品項快照判定 — 新增的訂單品項：`test_added_item_snapshots_current_pack_type`、`test_new_item_uses_current_spec_pack_type`
- [x] 前端試算 — 購物車未達免運：既有行為未動，`pricing.test.js`
- [x] 前端試算 — 購物車已達免運：既有行為未動，`pricing.test.js`
- [x] 前端試算 — 後台試算既有訂單品項：`orderEdit.test.js`「既有行沿用下單價與快照名稱」、`previewAmounts`
- [x] 前端試算 — 後台試算規格已刪除的兩粒裝：`orderEdit.test.js`「規格已刪除的兩粒裝 ×4 以 2 層試算,與後端一致」

## 留待之後
- 錯誤訊息改用快照名稱與正確用語：#83。
- GLOSSARY 與 admin-catalog 對包裝類型可否修改的落差：#84。
- ADR 補記包裝類型快照：#85。

## 下一步
- 無。

## Review
- 2026-10-30 `/review-and-fix`，範圍 `46da816..091b89e`：auto-fix 2、needs-decision 1、rejected 9、deferred 3。
- Needs decision：新測試的 `box` 命名與 GLOSSARY _Avoid_ 不符，但沿用既有測試慣例。
