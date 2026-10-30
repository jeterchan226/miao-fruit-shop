## 1. 成立時保存包裝類型

- [x] 1.1 寫失敗測試：顧客下單、代客下單、加訂新規格後，訂單品項與回應的 `is_two_pack` 為規格當下的值；後台訂單詳情同樣帶出
- [x] 1.2 `OrderItem` 新增 `is_two_pack`（NOT NULL、`server_default=false`）
- [x] 1.3 新增 Alembic migration：加欄位並依 `product_specs` 回填；`down_revision` 取 `alembic heads`
- [x] 1.4 `apply_items` 建立 `OrderItem` 時寫入規格的 `is_two_pack`
- [x] 1.5 `OrderItemRead` 新增必填 `is_two_pack`，更新 `order_service` 與 `admin_order_service` 的組裝點

## 2. 既有訂單品項改用快照

- [x] 2.1 寫失敗回歸測試：兩粒裝 ×4 的規格硬刪除後，修改同訂單其他訂單品項，運費仍以 2 層計算
- [x] 2.2 寫失敗測試：規格改包裝類型後編輯訂單，既有訂單品項層數與雙數檢查皆採快照；新增的訂單品項採規格現況
- [x] 2.3 新增 `_is_two_pack` helper，金額計算與雙數檢查都改用它；移除步驟 5 對規格的逐行查詢
- [x] 2.4 調整任何仍鎖定舊行為的既有測試

## 3. 後台試算

- [x] 3.1 寫失敗測試：`linesFromOrderItems` 對規格已刪除、`is_two_pack` 為 true 的項目回傳 `isTwoPack: true` 且 `locked: true`；總額試算以 2 層計算
- [x] 3.2 `linesFromOrderItems` 改讀 `it.is_two_pack`，更新註解與 `orderEdit.test.js` fixture

## 4. 文件

- [x] 4.1 `GLOSSARY.md`「訂單品項」定義補上包裝類型快照

## 5. 驗證

- [x] 5.1 手動驗證 migration：規格仍在、已下架、已刪除三種列的回填結果正確，`downgrade -1` 後可再 `upgrade head`
- [x] 5.2 `uv run ruff check .`、`uv run mypy app`、`uv run pytest -q` 全過
- [x] 5.3 `npm run test`、`npm run build` 全過
