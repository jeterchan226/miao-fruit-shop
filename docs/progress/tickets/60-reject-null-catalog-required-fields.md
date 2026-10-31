# #60 後台 PATCH 商品／規格對必填欄位送 null 回 500 而非 422

- 狀態：完成
- OpenSpec change：`reject-null-catalog-required-fields`（archive 後：`openspec/changes/archive/2026-10-30-reject-null-catalog-required-fields/`）
- Branch：`claude/sweet-davinci-8e56d2`
- 最後更新：2026-10-30

## 做了什麼
- 後台部分更新商品或規格時，必填欄位送 `null` 回 422，整筆不寫入（原為 500）。
- 選填欄位（商品圖片、標籤、標籤顏色；規格備註）送 `null` 維持清空。

## 決定與偏離
- 共用檢查放 `backend/app/schemas/validators.py` 的基底類別 `RejectNullRequiredFields`，子類設 `required_fields`。
- 偏離 [design.md](../../../openspec/changes/archive/2026-10-30-reject-null-catalog-required-fields/design.md)：design 寫共用 helper 純函式，review 時使用者決定改基底類別，商品、規格、訂單皆繼承，行為不變。
- 測試內另列一份必填欄位清單、不 import app 常數：常數漏列時測試才會失敗。
- 對不存在的 id 送必填 `null` 回 422 而非 404，因 schema 驗證先於查詢；spec 未定義，與訂單相同，不改。

## 驗收結果
- [x] 商品部分更新的 null 處理 — 商品必填欄位送 null：`test_update_product_required_field_null_is_422`（逐欄）
- [x] 商品部分更新的 null 處理 — 商品請求同時帶合法欄位：`test_update_product_null_with_valid_field_writes_nothing`
- [x] 商品部分更新的 null 處理 — 商品選填欄位送 null：`test_update_product_explicit_null_clears_optional_field`（逐欄）
- [x] 規格部分更新的 null 處理 — 規格必填欄位送 null：`test_update_spec_required_field_null_is_422`（逐欄）
- [x] 規格部分更新的 null 處理 — 規格請求同時帶合法欄位：`test_update_spec_null_with_valid_field_writes_nothing`
- [x] 規格部分更新的 null 處理 — 規格備註送 null：`test_update_spec_explicit_null_clears_note`

讀 `AdminApp.jsx` 確認後台前端不送必填 `null`：規格表單的數字欄位經 `Number()`，只有備註可能為 `null`；前端無商品更新呼叫。

## 留待之後
- GLOSSARY「規格名稱建立後不變」與 API 可改名稱的落差：#94。
- 後台表單未處理 422 的陣列 `detail`：#95。

## 下一步

## Review
- 2026-10-30 `/review-and-fix`：審查 `3ee4204..fd24adf`，共 11 項：auto-fix 3、needs-decision 2、rejected 4、deferred 2。
- needs-decision：三處 `_required_fields_not_null` 樣板是否改基底類別；兩個「同時帶合法欄位」測試是否參數化。建議都維持現狀。
- 2026-10-31 使用者決定：#4 改基底類別（`2db795e`），#5 維持現狀。最終 11 項：auto-fix 4、needs-decision 0、kept by user 1、rejected 4、deferred 2。
