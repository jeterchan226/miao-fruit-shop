## Context

`ProductUpdate`、`SpecUpdate` 的欄位都宣告為可 `null` 以支援省略，服務層以 `exclude_unset` 把請求帶的欄位全部寫入，必填欄位送 `null` 因此要到 commit 才被 NOT NULL 約束擋下並回 500。`AdminOrderUpdate` 已用 model validator 比對 `model_fields_set` 解決同一問題（#56）。後台規格表單只對備註送 `null`，其餘欄位永遠帶值。

必填與選填依資料表 nullable 判定：商品的 `image`、`tag`、`tag_color` 與規格的 `note` 可為 null，其餘皆 NOT NULL。

## Goals / Non-Goals

**Goals:**

- 商品、規格的必填欄位送 `null` 在請求驗證階段回 422，整筆不寫入。
- 選填欄位送 `null` 維持清空。
- 三個部分更新 schema 共用同一份檢查。

**Non-Goals:**

- 空字串、空白字串或負數等其他值驗證。
- 新增規格（`SpecCreate`）的驗證：必填欄位型別已不接受 `null`。
- 通用的資料庫約束錯誤轉 4xx 處理。
- 前端錯誤訊息呈現：後台前端不會送出此類請求。
- 用語或欄位可變性的調整（例如 GLOSSARY 稱規格名稱建立後不變，與現行 API 不同）。

## Decisions

- **在 schema 擋，不在服務層擋**：沿用 `AdminOrderUpdate` 的做法，讓錯誤走既有 422 回應。替代方案是服務層檢查後丟自訂例外，但要新增錯誤型別，且與訂單不一致。
- **抽共用 helper，三處共用**：在 `app/schemas/` 新增純函式，接收 model 與必填欄位名稱，對 `model_fields_set` 內值為 `None` 的欄位丟 `ValueError`，訊息沿用 `必填欄位不可為 null: <欄位>`。`AdminOrderUpdate._required_fields_not_null` 改呼叫它，行為不變。替代方案是在兩個 schema 各複製一份 validator，但會有三份相同邏輯。
- **必填欄位以明確常數列出**：比照 `ADMIN_ORDER_REQUIRED_FIELDS`，新增商品與規格各一組常數。替代方案是從 SQLAlchemy 欄位的 nullable 推導，但會讓 schema 依賴 models，破壞分層。欄位對應由參數化測試逐欄守住。
- **不改欄位型別**：欄位維持 `T | None = None`。改成不接受 `None` 的型別需要另一種「未帶」預設值，與既有 schema 風格不同且 mypy strict 不易通過。

## Testing Decisions

- **主要 entry point：HTTP API**。在 `backend/tests/test_admin_products_api.py` 以 `client` fixture 打 `PATCH /api/admin/products/{id}` 與 `PATCH /api/admin/specs/{id}`，用 `db_session` 建資料。這是可觀察行為的最高 seam，直接涵蓋「整筆不寫入」，且不綁 helper 內部。
- **逐欄參數化**：必填欄位每欄一組，避免常數漏列。
- **共用 helper 不另寫單元測試**：行為已由商品、規格新測試與訂單既有測試覆蓋。
- **Prior art**：`test_admin_orders_api.py` 的 `test_update_order_required_field_null_is_422`（參數化、同請求帶合法欄位、事後讀回驗證未寫入）與 `test_update_order_explicit_null_clears_optional_fields`。該檔既有測試也是訂單 validator 重構的回歸保護。

## Risks / Trade-offs

- 必填常數與資料表 nullable 不同步 → 未來新增欄位時可能漏列；由新增欄位的測試與 code review 把關。
- 其他 API 呼叫端若依賴 500 → 此路徑僅後台使用，且 422 仍屬失敗，無實際影響。
- #57 整併測試 factory 可能同時改動 `test_admin_products_api.py` → 僅為合併衝突，實作時以當下 dev 為準。
