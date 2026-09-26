## 1. 紅燈

- [ ] 1.1 `tests/test_order_amounts.py`：`compute_amounts` 回傳值沒有 `cod_fee` 屬性，`total == subtotal + shipping_fee`
- [ ] 1.2 `tests/test_orders_api.py`：201 回應與 409 `PRICE_CHANGED` 回應不含 `cod_fee`
- [ ] 1.3 `tests/test_admin_orders_api.py`：訂單詳情不含 `cod_fee`
- [ ] 1.4 確認上述測試失敗

## 2. 綠燈（第一階段：程式不再使用欄位）

- [ ] 2.1 `Amounts` 移除 `cod_fee`；`create_order`、`_replace_items` 不再指派
- [ ] 2.2 `OrderRead`、`AdminOrderRead`、`PriceChangedResponse`、`PriceChangedError`、`errors.py` handler、`_to_admin_order_read` 移除 `cod_fee`
- [ ] 2.3 `models/order.py` 移除 `cod_fee` mapped column
- [ ] 2.4 新增 migration：`orders.cod_fee` 加 `server_default '0'`
- [ ] 2.5 執行 1.x 測試通過

## 3. 前端

- [ ] 3.1 `AdminApp.jsx` 移除「貨到付款手續費」列
- [ ] 3.2 查詢正式資料 `payment_method = 'cod'` 筆數，為 0 則移除 `cod: '貨到付款'` 標籤
- [ ] 3.3 `npm run build` 通過；後台手動檢視訂單詳情

## 4. 第二階段：刪除欄位

- [ ] 4.1 新增 migration `drop_orders_cod_fee`（downgrade 加回 `NOT NULL DEFAULT 0`）
- [ ] 4.2 若 r09 已完成，確認 migration 一致性測試通過；否則手動 `upgrade head` / `downgrade -1` 驗證
- [ ] 4.3 第二階段於第一階段部署後、另一次部署才合併（PR 說明標註）

## 5. 重構與驗證

- [ ] 5.1 `grep -rn cod_fee backend/app frontend/src` 無結果（migration 檔除外）
- [ ] 5.2 在 backend/ 執行 `uv run pytest -q`、`uv run ruff check .`、`uv run mypy app`

## 6. 收尾

- [ ] 6.1 以 `refactor(order): 移除遺留的貨到付款手續費`（第一階段）與 `chore(db): 刪除 orders.cod_fee 欄位`（第二階段）提交
