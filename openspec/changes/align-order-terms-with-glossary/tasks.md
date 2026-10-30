## 1. 後端雙數限制訊息

- [ ] 1.1 在 `backend/tests/test_order_items.py` 把 `test_two_pack_odd_qty_raises_even_qty_required` 的規格名稱改為「精緻禮盒」，並斷言 `detail` 完整等於「精緻禮盒 為兩粒裝，請以雙數（2、4、6…）購買」，確認測試失敗
- [ ] 1.2 修改 `EvenQtyRequiredError` 的訊息為「兩粒裝」，確認測試通過

## 2. 前端雙數限制提示

- [ ] 2.1 把 `frontend/src/orderEdit.test.js` 模擬 `EVEN_QTY_REQUIRED` 的訊息改為新字串（透傳測試，改完應維持通過）
- [ ] 2.2 把 `Cart.jsx` 的 `EVEN_QTY_REQUIRED` 替代提示改為「兩粒裝商品請以雙數（2、4、6…）箱購買。」

## 3. 後台訂單畫面用語

- [ ] 3.1 把 `AdminApp.jsx` 訂單詳情檢視與編輯模式的區塊標題改為「訂單品項」，含區塊上方的註解
- [ ] 3.2 把 `AdminApp.jsx` 新訂單橫幅的替代摘要改為「訂單品項」

## 4. 後台規格表單用語

- [ ] 4.1 把 `AdminApp.jsx` 新增與編輯規格表單的選項改為「兩粒裝（須以雙數購買）」

## 5. 驗證

- [ ] 5.1 `grep -rn '商品明細\|為 2 粒裝\|2 粒裝（\|2 粒裝商品' frontend/src backend/app` 沒有結果
- [ ] 5.2 後端 `uv run ruff check .`、`uv run mypy app`、`uv run pytest -q` 通過
- [ ] 5.3 前端 `npm run test`、`npm run build` 通過
- [ ] 5.4 在 dev server 的後台確認訂單詳情（檢視與編輯）與規格表單顯示新用語
