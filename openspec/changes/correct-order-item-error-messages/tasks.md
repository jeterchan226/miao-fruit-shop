## 1. 雙數限制訊息用快照名稱

- [ ] 1.1 在 `backend/tests/test_order_items.py` 新增測試：既有兩粒裝訂單品項的規格改名後改奇數，`detail` 含快照名稱、不含現況名稱，確認測試失敗
- [ ] 1.2 修改 `apply_items` 的雙數限制訊息，既有訂單品項用 `spec_label`，新增的用規格現況名稱，確認測試通過

## 2. 庫存不足訊息用快照名稱

- [ ] 2.1 新增測試：既有訂單品項的規格改名後增量超過庫存，`detail` 含快照名稱、不含現況名稱，確認測試失敗
- [ ] 2.2 庫存不足訊息改用同一名稱規則，確認測試通過
- [ ] 2.3 新增測試：新增的訂單品項在雙數限制與庫存不足訊息中都用規格現況名稱

## 3. 後台 PRICE_CHANGED 提示

- [ ] 3.1 把 `frontend/src/orderEdit.test.js` 的 `PRICE_CHANGED` 測試改為「規格價格或包裝類型已更新，新的訂單總額為 NT$ 3,280，請重新確認後再儲存訂單。」，確認測試失敗
- [ ] 3.2 修改 `orderEditErrorMessage` 的提示，確認測試通過

## 4. 驗證

- [ ] 4.1 後端 `uv run ruff check .`、`uv run mypy app`、`uv run pytest -q` 通過
- [ ] 4.2 前端 `npm run test`、`npm run build` 通過
