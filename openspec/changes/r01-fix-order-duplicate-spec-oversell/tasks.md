## 1. 紅燈：撰寫失敗測試

- [x] 1.1 在 `tests/test_order_service.py` 新增「重複規格總量超過庫存回 `InsufficientStockError` 且庫存不變」測試
- [x] 1.2 新增「重複規格合併成單一 `OrderItem`、庫存正確扣減」測試
- [x] 1.3 新增「2 粒裝以合併數量判斷雙數」測試
- [x] 1.4 在 `tests/test_admin_order_service.py` 新增「後台重複規格超量編輯被拒、品項與庫存回滾」測試
- [x] 1.5 執行 `uv run pytest tests/test_order_service.py tests/test_admin_order_service.py -q`，確認新測試失敗且失敗原因符合預期

## 2. 綠燈：最小實作

- [x] 2.1 `order_service.create_order`：鎖定前先把 `data.items` 依 `spec_id` 合併數量
- [x] 2.2 `admin_order_service._replace_items`：同樣先合併 `new_items`
- [x] 2.3 重新執行 1.5 的測試，確認全部通過

## 3. 重構與驗證

- [x] 3.1 若兩處合併邏輯重複，抽成 `order_service._merge_item_qty()` 小函式（完整抽取留給 r22）
- [x] 3.2 在 backend/ 執行 `uv run pytest -q` 全綠
- [x] 3.3 執行 `uv run ruff check .` 與 `uv run mypy app`，本 change 不新增錯誤

## 4. 收尾

- [x] 4.1 以 `fix(order): 同規格品項合併計算庫存，避免超賣` 提交
